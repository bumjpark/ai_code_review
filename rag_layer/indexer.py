import shutil
import subprocess
import tempfile
from pathlib import Path

from rag_layer.chunking import PythonAstChunker
from rag_layer.qdrant_store import QdrantVectorStore


class RepositoryIndexer:
    def __init__(self, vector_store: QdrantVectorStore) -> None:
        self._vector_store = vector_store
        self._chunker = PythonAstChunker()

    def index_repository(self, github_url: str, branch: str | None = None) -> dict:
        temp_dir = Path(tempfile.mkdtemp(prefix="repo-index-"))
        indexed_files = 0
        all_chunks = []

        try:
            self._clone(github_url=github_url, branch=branch, target_dir=temp_dir)
            for file_path in temp_dir.rglob("*.py"):
                indexed_files += 1
                all_chunks.extend(self._chunker.chunk_file(root_dir=temp_dir, file_path=file_path))

            indexed_chunks = self._vector_store.upsert_chunks(github_url=github_url, chunks=all_chunks)
            return {
                "repository": github_url,
                "indexed_files": indexed_files,
                "indexed_chunks": indexed_chunks,
                "collection_name": self._vector_store.collection_name,
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _clone(self, github_url: str, branch: str | None, target_dir: Path) -> None:
        command = [
            "git",
            "clone",
            "--depth",
            "1",
        ]
        if branch:
            command.extend(["--branch", branch])
        command.extend([github_url, str(target_dir)])
        subprocess.run(command, check=True)
