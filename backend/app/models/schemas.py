from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class IndexRepositoryRequest(BaseModel):
    github_url: HttpUrl
    branch: str | None = None


class IndexRepositoryResponse(BaseModel):
    repository: str
    indexed_files: int
    indexed_chunks: int
    collection_name: str


class ReviewRequest(BaseModel):
    github_url: HttpUrl
    question: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=20)


class RetrieveRequest(BaseModel):
    github_url: HttpUrl
    query: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=20)


class RetrievedChunk(BaseModel):
    chunk_id: str
    file_path: str
    symbol: str
    start_line: int
    end_line: int
    score: float
    code: str


class Finding(BaseModel):
    severity: str
    title: str
    file_path: str
    line: int
    rationale: str
    recommendation: str


class ImprovedCode(BaseModel):
    file_path: str
    symbol: str
    code: str
    explanation: str


class ReviewResponse(BaseModel):
    summary: str
    findings: list[Finding]
    improved_code: list[ImprovedCode]
    retrieval_attempts: int
    used_query: str
    retrieved_context: list[RetrievedChunk]


class RetrievalDecision(BaseModel):
    sufficient: bool
    reason: str


class ReviewContext(BaseModel):
    question: str
    current_query: str
    retry_count: int = 0
    max_retries: int = 1
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    retrieval_decision: RetrievalDecision | None = None
    report: ReviewResponse | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrieveResponse(BaseModel):
    items: list[RetrievedChunk]
