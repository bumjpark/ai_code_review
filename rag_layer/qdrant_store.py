import hashlib
from typing import Iterable

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from backend.app.models.schemas import RetrievedChunk
from rag_layer.chunking import CodeChunk


class QdrantVectorStore:
    def __init__(
        self,
        url: str,
        api_key: str,
        collection_name: str,
        vector_size: int,
        embedding_model: str,
        openai_api_key: str,
    ) -> None:
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for embeddings.")
        self.collection_name = collection_name
        self._client = QdrantClient(url=url, api_key=api_key or None)
        self._vector_size = vector_size
        self._embedding_model = embedding_model
        self._openai = OpenAI(api_key=openai_api_key)

    def ensure_collection(self) -> None:
        collections = {item.name for item in self._client.get_collections().collections}
        if self.collection_name in collections:
            return
        self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
        )

    def upsert_chunks(self, github_url: str, chunks: Iterable[CodeChunk]) -> int:
        self.ensure_collection()
        points: list[PointStruct] = []
        count = 0

        for chunk in chunks:
            points.append(
                PointStruct(
                    id=self._stable_point_id(f"{github_url}:{chunk.chunk_id}"),
                    vector=self._embed(chunk.code),
                    payload={
                        "github_url": github_url,
                        "chunk_id": chunk.chunk_id,
                        "file_path": chunk.file_path,
                        "symbol": chunk.symbol,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "code": chunk.code,
                    },
                )
            )
            count += 1

        if points:
            self._client.upsert(collection_name=self.collection_name, points=points)
        return count

    def search(self, github_url: str, query: str, top_k: int) -> list[RetrievedChunk]:
        self.ensure_collection()
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="github_url",
                    match=MatchValue(value=github_url),
                )
            ]
        )
        query_vector = self._embed(query)

        if hasattr(self._client, "query_points"):
            response = self._client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False,
            )
            results = response.points
        else:
            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter,
            )
        chunks: list[RetrievedChunk] = []
        for item in results:
            payload = item.payload or {}
            chunks.append(
                RetrievedChunk(
                    chunk_id=str(payload["chunk_id"]),
                    file_path=str(payload["file_path"]),
                    symbol=str(payload["symbol"]),
                    start_line=int(payload["start_line"]),
                    end_line=int(payload["end_line"]),
                    score=float(item.score),
                    code=str(payload["code"]),
                )
            )
        return chunks

    def _stable_point_id(self, value: str) -> int:
        return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:16], 16)

    def _embed(self, text: str) -> list[float]:
        response = self._openai.embeddings.create(
            model=self._embedding_model,
            input=text,
        )
        vector = response.data[0].embedding
        if len(vector) != self._vector_size:
            raise ValueError(
                f"Embedding size mismatch: expected {self._vector_size}, got {len(vector)}."
            )
        return vector
