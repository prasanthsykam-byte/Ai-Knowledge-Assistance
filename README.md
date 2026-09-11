# Atlas Knowledge Assistant

A Python and Streamlit application for uploading study material and asking questions grounded in that material.

## Tech stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Language | Python 3.12+ | Application development |
| Frontend | Streamlit | Web interface, authentication flow, uploads, and chat |
| RAG framework | LangChain | Document splitting, retrieval, prompts, and model integration |
| Embeddings | Hugging Face Sentence Transformers (`all-MiniLM-L6-v2`) | Convert document chunks and questions into vectors |
| Vector database | ChromaDB | Store and search document embeddings per user |
| LLM | Google Gemini API | Generate answers from retrieved document context |
| Database | SQLite | Store users, document metadata, and extracted text |
| File parsing | `pypdf`, `python-docx`, `openpyxl` | Read PDF, DOCX, and XLSX files |
| Configuration | `python-dotenv` | Load `GEMINI_API_KEY` and other environment variables |
| Deployment | Streamlit Community Cloud, Render, or Railway | Host the Streamlit application |
| Version control | Git and GitHub | Track and publish source code |

## Run locally

1. Create a virtual environment: `python -m venv .venv`
2. Activate it on Windows: `.venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`.
5. Add your Google AI Studio key as `GEMINI_API_KEY`.
6. Start the app: `streamlit run app.py`

The app opens at `http://localhost:8501`. The same `GEMINI_API_KEY` environment variable works locally and in deployment secrets.

## Features

- Email/password accounts with salted `scrypt` password hashes
- Per-user document lists and delete controls
- TXT, Markdown, CSV, JSON, PDF, DOCX, and XLSX extraction
- Sentence Transformer embeddings persisted in ChromaDB
- LangChain similarity retrieval before Gemini generation
- Source passages shown with every answer
- 25 MB limit per file

## Project structure

```text
app.py                  Streamlit entrypoint and chat UI
rag/
	qa.py                 LangChain retrieval and Gemini answer generation
	vector_store.py       Sentence Transformer embeddings and ChromaDB
utils/
	database.py           SQLite users and document metadata
	document_loader.py    PDF, TXT, DOCX, and legacy format extraction
data/                   Local SQLite data
vectorstore/            ChromaDB persistence
```

## Deployment

Deploy `app.py` to Streamlit Community Cloud, Render, or Railway. Set the start command to `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT` where the platform requires one. Add `GEMINI_API_KEY` and optionally `GEMINI_MODEL` to the host's secret/environment settings.

SQLite, uploaded document text, and ChromaDB data are stored locally in `data/` and `vectorstore/`, both ignored by Git. For multiple replicas or durable production storage, replace SQLite with PostgreSQL and ChromaDB persistence with a managed vector database or shared volume.
