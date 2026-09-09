# Atlas Knowledge Assistant

A local web app that lets someone upload a set of documents and ask questions grounded in those documents.

## Accounts and file dashboard

Create an account or log in before uploading files. Passwords are stored locally as salted password hashes in `data/users.json`; session cookies are HTTP-only and last up to seven days (or until the app restarts). Each uploaded source belongs only to the signed-in account that added it. The dashboard shows that account's files and provides a delete control that removes the extracted data permanently.

Sources uploaded before accounts were enabled are intentionally not assigned to any account and will not appear in a dashboard.

## What it handles

- Text and Markdown: `.txt`, `.md`
- Structured data: `.csv`, `.json`
- Documents: `.pdf`, `.docx`
- Spreadsheets: `.xlsx`

Uploads are converted to text locally and stored under `data/`, which is ignored by Git. The original files are not retained. When AI answering is enabled, the assistant sends only the selected relevant passages and the question to Gemini; without a key, it keeps everything local and shows those passages directly.

## Run it

1. Install dependencies: `npm install`
2. Copy `.env.example` to `.env`.
3. Put your Google AI Studio key in `.env` as `GEMINI_API_KEY`. Do not put it in browser code or commit the file.
4. Start the app: `npm run dev`
5. Open `http://localhost:3000`

Without a key, upload and source retrieval still work; the app shows the relevant passages instead of generating a final answer.

## Important limits of this first version

- It accepts text-based PDFs. Scanned PDFs, images, audio, video, and handwritten notes need an OCR/transcription stage before they can be answered from.
- Each upload is limited to 25 MB and up to 10 files may be added per upload action.
- This is a single-user local application. For a shared or production system, add login, per-user storage, encrypted persistence, background ingestion, embeddings/vector search, and a managed database.
