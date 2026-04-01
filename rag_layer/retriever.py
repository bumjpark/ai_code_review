from rag_layer.qdrant_store import QdrantVectorStore


class CodeRetriever:
    def __init__(self, vector_store: QdrantVectorStore) -> None:
        self._vector_store = vector_store

    def retrieve(self, github_url: str, query: str, top_k: int):
        return self._vector_store.search(github_url=github_url, query=query, top_k=top_k)

