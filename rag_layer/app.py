from fastapi import FastAPI

from backend.app.config import settings
from backend.app.models.schemas import (
    IndexRepositoryRequest,
    IndexRepositoryResponse,
    RetrieveRequest,
    RetrieveResponse,
)
from rag_layer.indexer import RepositoryIndexer
from rag_layer.qdrant_store import QdrantVectorStore
from rag_layer.retriever import CodeRetriever

app = FastAPI(title="rag-service")


def build_vector_store() -> QdrantVectorStore:
    return QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
        vector_size=settings.qdrant_vector_size,
        embedding_model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/index", response_model=IndexRepositoryResponse)
def index_repository(request: IndexRepositoryRequest) -> IndexRepositoryResponse:
    indexer = RepositoryIndexer(vector_store=build_vector_store())
    result = indexer.index_repository(github_url=str(request.github_url), branch=request.branch)
    return IndexRepositoryResponse(**result)


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    retriever = CodeRetriever(vector_store=build_vector_store())
    items = retriever.retrieve(
        github_url=str(request.github_url),
        query=request.query,
        top_k=request.top_k,
    )
    return RetrieveResponse(items=items)
