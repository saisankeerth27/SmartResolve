"""Structured models for AI reasoning responses."""

from pydantic import BaseModel, Field


class PossibleCause(BaseModel):
    cause: str
    evidence: list[str]


class KnowledgeCitation(BaseModel):
    document_id: str
    document_title: str
    section: str


class AIReasoningResult(BaseModel):
    status: str = Field(description="grounded | insufficient_evidence")
    summary: str
    possible_causes: list[PossibleCause] = []
    recommended_next_steps: list[str] = []
    knowledge_citations: list[KnowledgeCitation] = []
    limitations: list[str] = []
    confidence: str = Field(description="high | medium | low")


class ReasoningRequest(BaseModel):
    question: str = "What is the most likely explanation for this case?"


class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    section_heading: str
    content: str
    score: float


class RetrievalResponse(BaseModel):
    status: str
    query: str
    results: list[RetrievalResult]
    total: int


class CaseReasoningResponse(BaseModel):
    case_id: str
    retrieval: RetrievalResponse
    reasoning: AIReasoningResult
