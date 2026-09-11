from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "knowledge.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                size INTEGER NOT NULL,
                added_at TEXT NOT NULL,
                text TEXT NOT NULL
            );
            """
        )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}:{digest.hex()}"


def password_matches(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":", 1)
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def authenticate(email: str, password: str, signup: bool) -> tuple[int | None, str | None]:
    normalized_email = " ".join(email.lower().split())
    if "@" not in normalized_email or "." not in normalized_email.rsplit("@", 1)[-1]:
        return None, "Enter a valid email address."
    if len(password) < 8:
        return None, "Use a password with at least 8 characters."
    with get_connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE email = ?", (normalized_email,)).fetchone()
        if signup:
            if user:
                return None, "An account with this email already exists."
            cursor = connection.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (normalized_email, hash_password(password), datetime.now(timezone.utc).isoformat()),
            )
            return cursor.lastrowid, None
        if not user or not password_matches(password, user["password_hash"]):
            return None, "Email or password is incorrect."
        return user["id"], None


def get_user(user_id: int):
    with get_connection() as connection:
        return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def list_documents(user_id: int):
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, name, size, added_at, text FROM documents WHERE user_id = ? ORDER BY added_at DESC",
            (user_id,),
        ).fetchall()


def save_document(user_id: int, name: str, size: int, text: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO documents (user_id, name, size, added_at, text) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, size, datetime.now(timezone.utc).isoformat(), text),
        )
        return cursor.lastrowid


def delete_document(document_id: int, user_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM documents WHERE id = ? AND user_id = ?", (document_id, user_id))
