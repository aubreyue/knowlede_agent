from __future__ import annotations

from pathlib import Path
from typing import Iterable

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils import DATA_DIR, VECTORSTORE_DIR, Settings


SUPPORTED_TEXT_EXTENSIONS = {".md", ".txt"}
SUPPORTED_EXTENSIONS = SUPPORTED_TEXT_EXTENSIONS | {".pdf"}


def _embedding_kwargs(settings: Settings) -> dict:
    kwargs = {
        "model": settings.embedding_model,
        "api_key": settings.openai_api_key,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return kwargs


def get_embeddings(settings: Settings) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(**_embedding_kwargs(settings))


def load_documents(data_dir: Path = DATA_DIR) -> list[Document]:
    documents: list[Document] = []

    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        if path.suffix.lower() in SUPPORTED_TEXT_EXTENSIONS:
            text = path.read_text(encoding="utf-8")
            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": str(path), "file_name": path.name},
                )
            )
            continue

        loader = PyPDFLoader(str(path))
        for doc in loader.load():
            doc.metadata["source"] = str(path)
            doc.metadata["file_name"] = path.name
            documents.append(doc)

    return documents


def list_supported_files(data_dir: Path = DATA_DIR) -> list[dict]:
    files: list[dict] = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        files.append(
            {
                "name": path.name,
                "path": str(path),
                "suffix": path.suffix.lower(),
                "size_kb": round(path.stat().st_size / 1024, 2),
            }
        )
    return files


def split_documents(documents: Iterable[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""],
    )
    return splitter.split_documents(list(documents))


def build_vectorstore(settings: Settings, data_dir: Path = DATA_DIR) -> int:
    documents = load_documents(data_dir)
    if not documents:
        raise ValueError(f"No supported documents found in {data_dir}")

    chunks = split_documents(documents)
    embeddings = get_embeddings(settings)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(str(VECTORSTORE_DIR))
    return len(chunks)


def load_vectorstore(settings: Settings) -> FAISS:
    index_file = VECTORSTORE_DIR / "index.faiss"
    if not index_file.exists():
        raise FileNotFoundError("Vector store not found. Please run ingestion first.")

    embeddings = get_embeddings(settings)
    return FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def vectorstore_exists() -> bool:
    return (VECTORSTORE_DIR / "index.faiss").exists()
