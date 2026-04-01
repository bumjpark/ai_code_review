import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CodeChunk:
    chunk_id: str
    file_path: str
    symbol: str
    start_line: int
    end_line: int
    code: str


class PythonAstChunker:
    def chunk_file(self, root_dir: Path, file_path: Path) -> list[CodeChunk]:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        relative_path = file_path.relative_to(root_dir).as_posix()
        lines = source.splitlines()
        chunks: list[CodeChunk] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = getattr(node, "end_lineno", node.lineno)
                code = "\n".join(lines[start - 1 : end])
                chunk_id = f"{relative_path}:{node.name}:{start}"
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        file_path=relative_path,
                        symbol=node.name,
                        start_line=start,
                        end_line=end,
                        code=code,
                    )
                )

        return chunks

