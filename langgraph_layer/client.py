import httpx

from backend.app.models.schemas import RetrieveRequest, RetrieveResponse


class RemoteCodeRetriever:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def retrieve(self, github_url: str, query: str, top_k: int):
        request = RetrieveRequest(github_url=github_url, query=query, top_k=top_k)
        response = httpx.post(
            f"{self._base_url}/retrieve",
            json=request.model_dump(mode="json"),
            timeout=60.0,
        )
        response.raise_for_status()
        payload = RetrieveResponse(**response.json())
        return payload.items
