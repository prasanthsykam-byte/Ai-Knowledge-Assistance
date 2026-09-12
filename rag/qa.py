from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from rag.vector_store import retrieve

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a patient knowledge assistant for beginner students. Answer only using the supplied context. "
            "If the answer is not in the context, say so plainly. Explain simply, use short paragraphs or numbered steps, "
            "and cite supporting passages as [1], [2], and so on. End with a brief Remember: line.\n\nContext:\n{context}",
        ),
        ("human", "Question: {question}"),
    ]
)


def answer_question(user_id: int, question: str) -> tuple[str, list[dict[str, str]]]:
    documents = retrieve(user_id, question)
    sources = [
        {"source": document.metadata.get("source", "Unknown"), "excerpt": document.page_content}
        for document in documents
    ]
    context = "\n\n".join(f"[{index}] {source['source']}\n{source['excerpt']}" for index, source in enumerate(sources, 1))
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "AI answering is not configured. Add GEMINI_API_KEY to your environment and restart the app.", sources
    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        google_api_key=api_key,
        temperature=0.2,
    )
    response = (PROMPT | model).invoke({"context": context, "question": question})
    return str(response.content), sources
