import httpx

from backend.app.models.schemas import (
    IndexRepositoryRequest,
    IndexRepositoryResponse,
    ReviewRequest,
    ReviewResponse,
)


class RAGClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def index_repository(self, request: IndexRepositoryRequest) -> IndexRepositoryResponse:
        response = httpx.post(
            f"{self._base_url}/index",
            json=request.model_dump(mode="json"),
            timeout=120.0,
        )
        response.raise_for_status()
        return IndexRepositoryResponse(**response.json())


class LangGraphClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def review(self, request: ReviewRequest) -> ReviewResponse:
        response = httpx.post(
            f"{self._base_url}/review",
            json=request.model_dump(mode="json"),
            timeout=120.0,
        )
        response.raise_for_status()
        return ReviewResponse(**response.json())


class ReviewService:
    def __init__(self, client: LangGraphClient) -> None:
        self._client = client

    def review(self, request: ReviewRequest) -> ReviewResponse:
        return self._client.review(request)


class IndexService:
    def __init__(self, client: RAGClient) -> None:
        self._client = client

    def index_repository(self, request: IndexRepositoryRequest) -> IndexRepositoryResponse:
        return self._client.index_repository(request)
