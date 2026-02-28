from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Person(BaseModel):
    family: Optional[str] = None
    given: Optional[str] = None
    literal: Optional[str] = None


class ProposalProvenance(BaseModel):
    source: str
    retrievedAt: datetime
    confidence: float = Field(ge=0.0, le=1.0)


class Proposal(BaseModel):
    id: str
    itemId: str
    stepId: str
    patch: List[Dict[str, Any]]
    provenance: ProposalProvenance
    rationale: str


class Issue(BaseModel):
    itemId: str
    stepId: str
    severity: Literal["error", "warning", "info"]
    message: str


class Diagnostic(BaseModel):
    stepId: str
    severity: str
    message: str


class CanonicalItem(BaseModel):
    id: str
    inputKey: str
    type: str
    title: str = ""
    authors: List[Person] = Field(default_factory=list)
    issued: Optional[str] = None
    accessed: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    publisher: Optional[str] = None
    containerTitle: Optional[str] = None
    identifiers: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    diagnostics: List[Diagnostic] = Field(default_factory=list)


class StepResult(BaseModel):
    stepId: str
    issues: List[Issue] = Field(default_factory=list)
    proposals: List[Proposal] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    sessionId: str
    inputFormat: Literal["bib", "rdf"]
    items: List[CanonicalItem]
    proposals: List[Proposal] = Field(default_factory=list)
    issues: List[Issue] = Field(default_factory=list)
    acceptedProposalIds: List[str] = Field(default_factory=list)


class DuplicateCluster(BaseModel):
    id: str
    itemIds: List[str]
    confidence: float
    reason: str


class ParseResponse(BaseModel):
    sessionId: str
    items: List[CanonicalItem]
    summary: Dict[str, Any]
