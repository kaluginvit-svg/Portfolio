from __future__ import annotations

import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv

from Haystack.haystack_agent import DEFAULT_KB_NAMESPACE
from pinecone_manager import PineconeManager


def _iter_knowledge_files(base_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.md", "*.txt"):
        files.extend(base_dir.rglob(pattern))
    return sorted(file for file in files if file.is_file())


def _make_chunk_id(relative_path: str, chunk_index: int) -> str:
    digest = hashlib.sha1(f"{relative_path}:{chunk_index}".encode("utf-8")).hexdigest()[:12]
    safe_path = relative_path.replace("\\", "/")
    return f"kb::{safe_path}::{chunk_index}::{digest}"


def main() -> None:
    load_dotenv()

    knowledge_dir = Path(os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base")).resolve()
    namespace = os.getenv("PINECONE_KB_NAMESPACE", DEFAULT_KB_NAMESPACE).strip() or DEFAULT_KB_NAMESPACE
    chunk_size = int(os.getenv("KNOWLEDGE_CHUNK_SIZE", "1200"))

    if not knowledge_dir.exists():
        raise FileNotFoundError(
            f"Папка knowledge base не найдена: {knowledge_dir}. "
            "Создай ее и положи туда .md или .txt файлы."
        )

    files = _iter_knowledge_files(knowledge_dir)
    if not files:
        raise ValueError(f"В папке {knowledge_dir} нет .md или .txt файлов для индексации.")

    manager = PineconeManager()

    total_chunks = 0
    for file_path in files:
        relative_path = file_path.relative_to(knowledge_dir).as_posix()
        text = file_path.read_text(encoding="utf-8")
        chunks = manager.chunk_text(text, chunk_size=chunk_size)

        documents = []
        for chunk_index, chunk_text in enumerate(chunks, start=1):
            documents.append(
                {
                    "id": _make_chunk_id(relative_path, chunk_index),
                    "text": chunk_text,
                    "metadata": {
                        "doc_type": "knowledge",
                        "source_path": relative_path,
                        "title": file_path.stem,
                        "chunk_index": chunk_index,
                        "chunk_total": len(chunks),
                    },
                }
            )

        manager.upsert_documents(documents, namespace=namespace)
        total_chunks += len(documents)
        print(f"Indexed {relative_path}: {len(documents)} chunks")

    print(f"Done. Indexed {len(files)} files and {total_chunks} chunks into namespace `{namespace}`.")


if __name__ == "__main__":
    main()
