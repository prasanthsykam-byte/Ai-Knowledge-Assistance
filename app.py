from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from rag.qa import answer_question
from rag.vector_store import delete_document_vectors, index_document
from utils.database import (
    authenticate,
    delete_document,
    get_user,
    initialize_database,
    list_documents,
    save_document,
)
from utils.document_loader import SUPPORTED_EXTENSIONS, extract_text, to_document

load_dotenv()

st.set_page_config(page_title="Atlas Knowledge Assistant", page_icon="A", layout="wide")
initialize_database()
st.session_state.setdefault("messages", [])


def apply_nature_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --forest: #1d4d38;
            --forest-deep: #123527;
            --moss: #6f955c;
            --sage: #d8e7cd;
            --leaf: #edf5e8;
            --paper: #f8fbf5;
            --ink: #193126;
            --muted: #64776a;
            --line: #d7e4d2;
        }

        .stApp {
            background: radial-gradient(circle at 92% 4%, #dcebd6 0, transparent 27rem), linear-gradient(135deg, var(--paper), #f2f8ef 60%, #e7f1e2);
            color: var(--ink);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"] { max-width: 1040px; padding: 3.5rem 2.5rem 5rem; }
        [data-testid="stVerticalBlock"] { gap: 0.85rem; }
        h1 { font-size: clamp(2rem, 4vw, 3.35rem); line-height: 1.02; margin-bottom: .4rem; }
        h2, h3 { color: var(--forest-deep); letter-spacing: -0.03em; }
        [data-testid="stCaptionContainer"] { color: var(--muted); }
        [data-testid="stSidebar"] {
            background: linear-gradient(165deg, #123527 0%, #1d4d38 58%, #296148 100%);
            border-right: 0;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding: 2.2rem 1.3rem; }
        [data-testid="stSidebar"] * { color: #f4f8f0; }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #c9ddc5; }
        [data-testid="stSidebar"] hr { border-color: #ffffff26; margin: 1.35rem 0; }
        [data-testid="stSidebar"] h2 { font-size: 1.5rem; color: #ffffff; margin-bottom: 0; }
        [data-testid="stSidebar"] h3 { color: #e1efd9; font-size: .78rem; text-transform: uppercase; letter-spacing: .13em; }
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
            background: #ffffff10;
            border: 1px dashed #b8d2ae;
            border-radius: 13px;
        }
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            background: #ffffff12;
            border-color: #9fbea0;
            color: #f4f8f0;
        }
        .brand-lockup { display: flex; align-items: center; gap: .75rem; margin-bottom: 2.2rem; }
        .brand-mark { display: grid; place-items: center; width: 2.6rem; height: 2.6rem; border-radius: 12px 12px 12px 4px; background: var(--forest); color: white; font-weight: 800; font-size: 1.2rem; box-shadow: 0 8px 18px #1d4d3833; }
        .brand-name { color: var(--forest-deep); font-size: 1rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
        .auth-intro { max-width: 36rem; margin: 1rem auto 2rem; text-align: center; }
        .auth-intro p { color: var(--muted); font-size: 1rem; line-height: 1.6; }
        [data-testid="stForm"] { border: 1px solid var(--line); border-radius: 20px; background: #ffffffc9; padding: 1.6rem; box-shadow: 0 18px 50px #1d4d3814; }
        [data-testid="stTextInput"] input,
        [data-testid="stChatInput"] textarea,
        [data-testid="stFileUploaderDropzone"] input {
            color: var(--ink) !important;
            caret-color: var(--forest) !important;
        }
        [data-testid="stTextInput"] input { border-radius: 10px; border-color: #c7d8c3; background: #fbfdf9; }
        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stChatInput"] textarea::placeholder { color: #829187 !important; opacity: 1; }
        [data-testid="stTextInput"] input:focus { border-color: var(--moss); box-shadow: 0 0 0 1px var(--moss); }
        [data-testid="stToggle"] { margin: 0 auto 1.2rem; max-width: 23rem; }
        .section-kicker { color: var(--moss); font-size: .72rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; margin-bottom: .55rem; }
        .dashboard-intro { padding: 1.5rem 1.7rem; margin-bottom: 1.5rem; border: 1px solid var(--line); border-radius: 18px; background: #ffffff99; box-shadow: 0 12px 34px #1d4d380d; }
        .dashboard-intro p { margin: 0; color: var(--muted); }
        [data-testid="stChatMessage"] {
            border: 1px solid var(--line);
            border-radius: 18px;
            background: #ffffffd1;
            box-shadow: 0 8px 28px #214e3b12;
            margin: .7rem 0;
            padding: 1.15rem 1.3rem;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong {
            color: var(--ink) !important;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background: #e8f2e3;
            border-color: #c5dabe;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            background: #fffffccc;
        }
        [data-testid="stChatInput"] {
            background: #ffffffef;
            border-color: #aac59f;
            box-shadow: 0 10px 30px #214e3b1c;
        }
        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] textarea:focus {
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
            background-color: #ffffff !important;
            border-color: var(--moss);
        }
        [data-testid="stChatInput"] textarea::placeholder { color: #64776a !important; opacity: 1 !important; }
        [data-testid="stChatInput"] [contenteditable="true"],
        [data-testid="stChatInput"] [contenteditable="true"]:focus {
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
            caret-color: var(--forest) !important;
        }
        [data-testid="stMarkdownContainer"] { color: var(--ink); }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li { color: var(--ink); }
        .stButton > button, .stFormSubmitButton > button {
            min-height: 2.65rem;
            border-radius: 10px;
            border: 1px solid var(--moss);
            color: var(--forest-deep);
            background: var(--sage);
            font-weight: 650;
            transition: background .2s ease, transform .2s ease;
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover {
            border-color: var(--forest);
            background: #c5dbb9;
            color: var(--forest-deep);
            transform: translateY(-1px);
        }
        .stFormSubmitButton > button[kind="primary"], .stButton > button[kind="primary"] {
            background: var(--forest);
            border-color: var(--forest);
            color: white;
        }
        .stFormSubmitButton > button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover { background: var(--forest-deep); color: white; }
        [data-testid="stExpander"] {
            border-color: #c8dcc2;
            border-radius: 12px;
            background: #ffffff99;
        }
        [data-testid="stAlert"] { border-radius: 12px; border: 0; }
        @media (max-width: 700px) {
            [data-testid="stMainBlockContainer"] { padding: 2rem 1rem 4.5rem; }
            .dashboard-intro { padding: 1.1rem; }
            [data-testid="stChatMessage"] { padding: .95rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_auth() -> None:
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.markdown('<div class="brand-lockup"><div class="brand-mark">A</div><div class="brand-name">Atlas</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-intro"><h1>Knowledge, gathered.</h1><p>Your private study desk for turning documents into clear, grounded answers.</p></div>', unsafe_allow_html=True)
        signup = st.toggle("Create a new account")
        with st.form("auth_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create account" if signup else "Log in", type="primary", use_container_width=True)
    if submitted:
        user_id, error = authenticate(email, password, signup)
        if error:
            st.error(error)
        else:
            st.session_state.user_id = user_id
            st.rerun()


def render_sources(sources: list[dict[str, str]]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for index, source in enumerate(sources, 1):
            st.markdown(f"**[{index}] {source['source']}**")
            st.caption(source["excerpt"])


def render_sidebar(user) -> None:
    with st.sidebar:
        st.header("Atlas")
        st.caption(user["email"])
        if st.button("Log out"):
            st.session_state.pop("user_id", None)
            st.session_state.messages = []
            st.rerun()
        st.divider()
        st.subheader("Add knowledge")
        upload_files = st.file_uploader(
            "Choose PDF, TXT, DOCX, or supported text files",
            type=[extension.removeprefix(".") for extension in SUPPORTED_EXTENSIONS],
            accept_multiple_files=True,
        )
        if st.button("Index files", type="primary", disabled=not upload_files):
            for upload_file in upload_files:
                try:
                    text = extract_text(upload_file).strip()
                    if not text:
                        raise ValueError("The file did not contain readable text.")
                    document_id = save_document(user["id"], upload_file.name, upload_file.size, text)
                    chunk_count = index_document(user["id"], to_document(text, upload_file.name, document_id, user["id"]))
                    st.success(f"{upload_file.name}: indexed {chunk_count} chunks")
                except Exception as error:
                    st.error(f"{upload_file.name}: {error}")
            st.rerun()
        st.divider()
        st.subheader("Your files")
        for document in list_documents(user["id"]):
            st.caption(f"{document['name']} ({max(1, round(document['size'] / 1024))} KB)")
            if st.button("Delete", key=f"delete-{document['id']}"):
                delete_document_vectors(user["id"], document["id"])
                delete_document(document["id"], user["id"])
                st.rerun()


def render_chat(user) -> None:
    document_count = len(list_documents(user["id"]))
    st.markdown(f'<div class="dashboard-intro"><div class="section-kicker">Your study desk</div><h1>Ask your knowledge</h1><p>{document_count} indexed file{"s" if document_count != 1 else ""} ready to explore.</p></div>', unsafe_allow_html=True)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            render_sources(message.get("sources", []))
    question = st.chat_input("Ask a question about your files")
    if not question:
        return
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    try:
        with st.chat_message("assistant"):
            with st.spinner("Searching your knowledge..."):
                answer, sources = answer_question(user["id"], question)
            st.markdown(answer)
            render_sources(sources)
        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
    except Exception as error:
        st.error(f"Could not answer that question: {error}")


user_id = st.session_state.get("user_id")
user = get_user(user_id) if user_id else None
apply_nature_theme()
if user:
    render_sidebar(user)
    render_chat(user)
else:
    render_auth()
