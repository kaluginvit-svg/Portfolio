"""

Haystack Pipeline: Docling → markdown → чанки → Pinecone (user_file metadata).

"""



from __future__ import annotations



import hashlib

import logging

from pathlib import Path

from typing import TYPE_CHECKING



from haystack import Pipeline, component



if TYPE_CHECKING:

    from pinecone_manager import PineconeManager



logger = logging.getLogger(__name__)





@component

class DoclingMarkdownComponent:

    """Конвертация локального файла в Markdown через Docling."""



    @component.output_types(markdown=str)

    def run(self, file_path: str) -> dict[str, str]:

        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

        from docling.document_converter import DocumentConverter, PdfFormatOption

        from docling.datamodel.base_models import InputFormat

        from docling.datamodel.pipeline_options import PdfPipelineOptions



        path = (file_path or "").strip()

        if not path or not Path(path).is_file():

            raise ValueError("Некорректный путь к файлу для Docling.")

        # pypdfium2 вместо docling_parse: на Windows нативный парсер часто ломает пути к pdf_resources/glyphs.

        converter = DocumentConverter(

            format_options={

                InputFormat.PDF: PdfFormatOption(

                    pipeline_options=PdfPipelineOptions(),

                    backend=PyPdfiumDocumentBackend,

                )

            },

        )

        result = converter.convert(path)

        md = result.document.export_to_markdown()

        text = (md or "").strip()

        if not text:

            raise ValueError("Docling вернул пустой текст — попробуйте другой файл.")

        return {"markdown": text}





@component

class UserFilePineconeWriter:

    """Чанкинг и upsert в Pinecone с метаданными файла пользователя."""



    def __init__(self, manager: "PineconeManager", namespace: str, chunk_size: int) -> None:

        self._manager = manager

        self._namespace = namespace

        self._chunk_size = chunk_size



    @component.output_types(stored_chunks=int)

    def run(self, markdown: str, user_id: int, filename: str) -> dict[str, int]:

        uid = int(user_id)

        name = (filename or "document").strip() or "document"

        chunks = self._manager.chunk_text(markdown, chunk_size=self._chunk_size)

        if not chunks:

            raise ValueError("Не удалось разбить документ на чанки.")



        digest = hashlib.sha1(f"{uid}:{name}".encode("utf-8")).hexdigest()[:12]

        safe_name = name.replace("\\", "/")



        documents: list[dict] = []

        for idx, chunk_text in enumerate(chunks, start=1):

            doc_id = f"uf::{uid}::{digest}::{idx}"

            documents.append(

                {

                    "id": doc_id,

                    "text": chunk_text,

                    "metadata": {

                        "doc_type": "user_file",

                        "user_id": uid,

                        "filename": name,

                        "chunk_index": idx,

                        "chunk_total": len(chunks),

                        "source_path": safe_name,

                        "title": Path(name).stem,

                    },

                }

            )



        self._manager.upsert_documents(documents, namespace=self._namespace)

        logger.info("Pinecone upsert user_file uid=%s chunks=%s", uid, len(documents))

        return {"stored_chunks": len(documents)}





def build_user_file_ingestion_pipeline(

    manager: "PineconeManager",

    *,

    namespace: str,

    chunk_size: int,

) -> Pipeline:

    pipeline = Pipeline()

    pipeline.add_component("docling", DoclingMarkdownComponent())

    pipeline.add_component(

        "store",

        UserFilePineconeWriter(manager, namespace=namespace, chunk_size=chunk_size),

    )

    pipeline.connect("docling.markdown", "store.markdown")

    return pipeline





def run_ingestion(

    *,

    pipeline: Pipeline,

    file_path: str,

    user_id: int,

    filename: str,

) -> tuple[str, int]:

    """

    Запускает pipeline; возвращает (markdown из Docling, число сохранённых чанков).

    """

    out = pipeline.run(

        {

            "docling": {"file_path": file_path},

            "store": {"user_id": user_id, "filename": filename},

        },

        include_outputs_from={"docling", "store"},

    )

    md = str((out.get("docling") or {}).get("markdown") or "").strip()

    stored = int((out.get("store") or {}).get("stored_chunks") or 0)

    return md, stored


