from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from rapidfuzz import fuzz

from app.models.schema import CanonicalItem, DuplicateCluster, Issue, Proposal, ProposalProvenance, StepResult
from app.services.resolvers import ResolverService


@dataclass
class PipelineContext:
    resolver: ResolverService


class PipelineStep:
    id: str
    name: str

    async def run(self, items: List[CanonicalItem], ctx: PipelineContext) -> StepResult:
        raise NotImplementedError


class RequiredFieldsStep(PipelineStep):
    id = "required_fields"
    name = "Validate required fields"

    async def run(self, items: List[CanonicalItem], ctx: PipelineContext) -> StepResult:
        issues: List[Issue] = []
        for item in items:
            for field in ("title", "type", "url"):
                value = getattr(item, field)
                if not value:
                    issues.append(Issue(itemId=item.id, stepId=self.id, severity="error", message=f"Missing required field: {field}"))
        return StepResult(stepId=self.id, issues=issues, stats={"missing": len(issues)})


class UrlValidationStep(PipelineStep):
    id = "url_validation"
    name = "Validate URLs"

    async def run(self, items: List[CanonicalItem], ctx: PipelineContext) -> StepResult:
        proposals: List[Proposal] = []
        issues: List[Issue] = []
        for item in items:
            if not item.url:
                continue
            result = await ctx.resolver.validate_url(item.url)
            if not result.get("ok"):
                issues.append(Issue(itemId=item.id, stepId=self.id, severity="warning", message=f"URL invalid: {item.url}"))
                continue
            final_url = result.get("finalUrl")
            if final_url and final_url != item.url:
                proposals.append(
                    Proposal(
                        id=str(uuid.uuid4()),
                        itemId=item.id,
                        stepId=self.id,
                        patch=[{"op": "replace", "path": "/url", "value": final_url}],
                        provenance=ProposalProvenance(source="httpx", retrievedAt=datetime.now(timezone.utc), confidence=0.95),
                        rationale="Canonical URL from redirect target",
                    )
                )
        return StepResult(stepId=self.id, issues=issues, proposals=proposals, stats={"checked": len(items)})


class DoiStep(PipelineStep):
    id = "doi_enrichment"
    name = "Ensure and validate DOI"

    async def run(self, items: List[CanonicalItem], ctx: PipelineContext) -> StepResult:
        proposals: List[Proposal] = []
        issues: List[Issue] = []
        for item in items:
            if item.doi:
                csl = await ctx.resolver.resolve_doi_csl(item.doi)
                if not csl:
                    issues.append(Issue(itemId=item.id, stepId=self.id, severity="warning", message="DOI did not resolve"))
                continue
            crossref = await ctx.resolver.resolve_by_title(item.title)
            if crossref and crossref.get("DOI"):
                proposals.append(
                    Proposal(
                        id=str(uuid.uuid4()),
                        itemId=item.id,
                        stepId=self.id,
                        patch=[{"op": "add", "path": "/doi", "value": crossref["DOI"].lower()}],
                        provenance=ProposalProvenance(source="crossref", retrievedAt=datetime.now(timezone.utc), confidence=0.74),
                        rationale="DOI inferred from Crossref title lookup",
                    )
                )
        return StepResult(stepId=self.id, issues=issues, proposals=proposals, stats={"proposed": len(proposals)})


class MetadataEnrichmentStep(PipelineStep):
    id = "metadata_enrichment"
    name = "Enrich metadata"

    async def run(self, items: List[CanonicalItem], ctx: PipelineContext) -> StepResult:
        proposals: List[Proposal] = []
        for item in items:
            if not item.doi:
                continue
            csl = await ctx.resolver.resolve_doi_csl(item.doi)
            if not csl:
                continue
            patch = []
            if csl.get("title") and csl.get("title") != item.title:
                patch.append({"op": "replace", "path": "/title", "value": csl["title"]})
            if csl.get("publisher") and csl.get("publisher") != item.publisher:
                patch.append({"op": "replace", "path": "/publisher", "value": csl["publisher"]})
            if csl.get("container-title") and csl.get("container-title") != item.containerTitle:
                patch.append({"op": "replace", "path": "/containerTitle", "value": csl["container-title"]})
            if patch:
                proposals.append(
                    Proposal(
                        id=str(uuid.uuid4()),
                        itemId=item.id,
                        stepId=self.id,
                        patch=patch,
                        provenance=ProposalProvenance(source="doi-csl", retrievedAt=datetime.now(timezone.utc), confidence=0.88),
                        rationale="Metadata from DOI content negotiation",
                    )
                )
        return StepResult(stepId=self.id, proposals=proposals, stats={"enriched": len(proposals)})


class NormalizeStep(PipelineStep):
    id = "normalization"
    name = "Normalize types and publishers"
    TYPE_MAP = {"article": "article-journal", "inproceedings": "paper-conference", "misc": "webpage"}

    async def run(self, items: List[CanonicalItem], ctx: PipelineContext) -> StepResult:
        proposals: List[Proposal] = []
        for item in items:
            t = self.TYPE_MAP.get(item.type.lower())
            patch = []
            if t and t != item.type:
                patch.append({"op": "replace", "path": "/type", "value": t})
            if item.publisher:
                normalized = item.publisher.strip().title()
                if normalized != item.publisher:
                    patch.append({"op": "replace", "path": "/publisher", "value": normalized})
            if patch:
                proposals.append(
                    Proposal(
                        id=str(uuid.uuid4()), itemId=item.id, stepId=self.id, patch=patch,
                        provenance=ProposalProvenance(source="normalizer", retrievedAt=datetime.now(timezone.utc), confidence=0.93),
                        rationale="Mapped to canonical vocabulary"
                    )
                )
        return StepResult(stepId=self.id, proposals=proposals, stats={"normalized": len(proposals)})


class AccessedDateStep(PipelineStep):
    id = "accessed_date"
    name = "Add accessed dates"

    async def run(self, items: List[CanonicalItem], ctx: PipelineContext) -> StepResult:
        web_types = {"webpage", "post", "misc"}
        proposals: List[Proposal] = []
        today = datetime.now(timezone.utc).date().isoformat()
        for item in items:
            if item.type in web_types and not item.accessed:
                proposals.append(
                    Proposal(
                        id=str(uuid.uuid4()), itemId=item.id, stepId=self.id,
                        patch=[{"op": "add", "path": "/accessed", "value": today}],
                        provenance=ProposalProvenance(source="policy", retrievedAt=datetime.now(timezone.utc), confidence=1.0),
                        rationale="Web-like item requires accessed date"
                    )
                )
        return StepResult(stepId=self.id, proposals=proposals, stats={"added": len(proposals)})


def detect_duplicates(items: List[CanonicalItem], threshold: int = 90) -> List[DuplicateCluster]:
    clusters: List[DuplicateCluster] = []
    by_doi = {}
    for item in items:
        if item.doi:
            by_doi.setdefault(item.doi.lower(), []).append(item.id)
    for doi, ids in by_doi.items():
        if len(ids) > 1:
            clusters.append(DuplicateCluster(id=f"doi:{doi}", itemIds=ids, confidence=1.0, reason="Exact DOI match"))

    used = set(i for c in clusters for i in c.itemIds)
    for i, a in enumerate(items):
        if a.id in used:
            continue
        group = [a.id]
        for b in items[i + 1 :]:
            if b.id in used:
                continue
            score = fuzz.token_set_ratio((a.title or "").lower(), (b.title or "").lower())
            if score >= threshold:
                group.append(b.id)
        if len(group) > 1:
            conf = min(0.99, threshold / 100)
            clusters.append(DuplicateCluster(id=str(uuid.uuid4()), itemIds=group, confidence=conf, reason="Fuzzy title cluster"))
            used.update(group)
    return clusters


PIPELINE_STEPS = [
    RequiredFieldsStep(),
    UrlValidationStep(),
    DoiStep(),
    MetadataEnrichmentStep(),
    NormalizeStep(),
    AccessedDateStep(),
]
