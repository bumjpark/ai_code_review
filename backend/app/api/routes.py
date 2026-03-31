from fastapi import APIRouter, Depends

from backend.app.config import settings
from backend.app.models.schemas import (
    IndexRepositoryRequest,
    IndexRepositoryResponse,
    ReviewRequest,
    ReviewResponse,
)
from backend.app.services.review_service import IndexService, LangGraphClient, RAGClient, ReviewService

router = APIRouter()


def get_rag_client() -> RAGClient:
    return RAGClient(base_url=settings.rag_service_url)


def get_langgraph_client() -> LangGraphClient:
    return LangGraphClient(base_url=settings.langgraph_service_url)


def get_review_service(
    client: LangGraphClient = Depends(get_langgraph_client),
) -> ReviewService:
    return ReviewService(client=client)


def get_index_service(
    client: RAGClient = Depends(get_rag_client),
) -> IndexService:
    return IndexService(client=client)


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/index", response_model=IndexRepositoryResponse)
def index_repository(
    request: IndexRepositoryRequest,
    service: IndexService = Depends(get_index_service),
) -> IndexRepositoryResponse:
    return service.index_repository(request)


@router.post("/review", response_model=ReviewResponse)
def review_repository(
    request: ReviewRequest,
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    return service.review(request)
