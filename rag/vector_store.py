from __future__ import annotations

import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = Path(__file__).resolve().parents[1]
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True})


def get_vectorstore(user_id: int) -> Chroma:
    VECTORSTORE_DIR.mkdir(exist_ok=True)
    return Chroma(
        collection_name=f"knowledge_user_{user_id}",
        embedding_function=get_embeddings(),
        persist_directory=str(VECTORSTORE_DIR),
    )


def index_document(user_id: int, document) -> int:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=180, separators=["\n\n", "\n", ". ", " ", ""])
    chunks = splitter.split_documents([document])
    ids = [f"document-{document.metadata['document_id']}-chunk-{index}" for index in range(len(chunks))]
    get_vectorstore(user_id).add_documents(chunks, ids=ids)
    return len(chunks)


def delete_document_vectors(user_id: int, document_id: int) -> None:
    get_vectorstore(user_id).delete(where={"document_id": str(document_id)})


def retrieve(user_id: int, question: str, count: int = 6):
    return get_vectorstore(user_id).as_retriever(search_type="similarity", search_kwargs={"k": count}).invoke(question)


def clear_vectorstore() -> None:
    if VECTORSTORE_DIR.exists():
        shutil.rmtree(VECTORSTORE_DIR)
