from __future__ import annotations

import io
import json
import uuid
from typing import Dict, List, Literal

import jsonpatch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.exporters.bibtex_exporter import export_bibtex
from app.exporters.rdf_exporter import export_rdf
from app.models.schema import ParseResponse, Proposal, SessionState
from app.parsers.bibtex_parser import parse_bibtex
from app.parsers.rdf_parser import parse_rdf
from app.pipeline.steps import PIPELINE_STEPS, PipelineContext, detect_duplicates
from app.services.cache import ResolverCache
from app.services.resolvers import ResolverService

app = FastAPI(title="Bibliography Hardening Workbench")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

sessions: Dict[str, SessionState] = {}
resolver = ResolverService(ResolverCache())


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/api/parse", response_model=ParseResponse)
async def parse_file(format: Literal["bib", "rdf"] = Form(...), file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    items = parse_bibtex(content) if format == "bib" else parse_rdf(content)
    session_id = str(uuid.uuid4())
    sessions[session_id] = SessionState(sessionId=session_id, inputFormat=format, items=items)
    return ParseResponse(sessionId=session_id, items=items, summary={"count": len(items), "format": format})


@app.post("/api/sessions/{session_id}/run")
async def run_pipeline(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    ctx = PipelineContext(resolver=resolver)
    all_results = []
    proposals: List[Proposal] = []
    issues = []
    for step in PIPELINE_STEPS:
        result = await step.run(session.items, ctx)
        all_results.append(result)
        proposals.extend(result.proposals)
        issues.extend(result.issues)
    session.proposals = proposals
    session.issues = issues
    sessions[session_id] = session
    return {"steps": all_results, "proposals": proposals, "issues": issues, "duplicates": detect_duplicates(session.items)}


@app.post("/api/sessions/{session_id}/proposals/{proposal_id}/accept")
async def accept_proposal(session_id: str, proposal_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    proposal = next((p for p in session.proposals if p.id == proposal_id), None)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    idx = next((i for i, item in enumerate(session.items) if item.id == proposal.itemId), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Item not found")
    original = session.items[idx].model_dump()
    patched = jsonpatch.apply_patch(original, proposal.patch, in_place=False)
    session.items[idx] = session.items[idx].model_validate(patched)
    session.acceptedProposalIds.append(proposal.id)
    return {"ok": True, "item": session.items[idx]}


@app.post("/api/sessions/{session_id}/proposals/{proposal_id}/reject")
async def reject_proposal(session_id: str, proposal_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.proposals = [p for p in session.proposals if p.id != proposal_id]
    return {"ok": True}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/api/sessions/{session_id}/duplicates")
async def get_duplicates(session_id: str, threshold: int = 90):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"clusters": detect_duplicates(session.items, threshold=threshold)}


@app.post("/api/sessions/{session_id}/merge")
async def merge_duplicates(session_id: str, payload: dict):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    canonical = payload["canonicalItemId"]
    merge_items = set(payload.get("mergeItemIds", []))
    field_overrides = payload.get("fieldOverrides", {})
    target = next((item for item in session.items if item.id == canonical), None)
    if not target:
        raise HTTPException(status_code=404, detail="Canonical item missing")
    for field, value in field_overrides.items():
        setattr(target, field, value)
    session.items = [item for item in session.items if item.id == canonical or item.id not in merge_items]
    return {"ok": True, "count": len(session.items)}


@app.get("/api/sessions/{session_id}/export")
async def export(session_id: str, format: Literal["bib", "rdf", "audit", "csv", "md"]):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if format == "bib":
        return PlainTextResponse(export_bibtex(session.items), media_type="text/plain")
    if format == "rdf":
        return PlainTextResponse(export_rdf(session.items), media_type="application/rdf+xml")
    if format == "audit":
        return PlainTextResponse(json.dumps({"accepted": session.acceptedProposalIds, "proposals": [p.model_dump(mode='json') for p in session.proposals]}, indent=2), media_type="application/json")
    if format == "csv":
        out = io.StringIO()
        out.write("id,title,type,url,doi\n")
        for it in session.items:
            out.write(f'"{it.id}","{it.title}","{it.type}","{it.url or ""}","{it.doi or ""}"\n')
        return PlainTextResponse(out.getvalue(), media_type="text/csv")
    md = "| ID | Title | Type | URL | DOI |\n|---|---|---|---|---|\n"
    for it in session.items:
        md += f"| {it.inputKey} | {it.title} | {it.type} | {it.url or ''} | {it.doi or ''} |\n"
    return PlainTextResponse(md, media_type="text/markdown")
