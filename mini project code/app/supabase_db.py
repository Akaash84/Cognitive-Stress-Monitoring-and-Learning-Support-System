import os
from datetime import datetime
from typing import List, Tuple

from passlib.context import CryptContext
from supabase import Client, create_client

# Use PBKDF2-SHA256 to avoid bcrypt's 72-byte password limit and platform-specific bcrypt backends.
_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Optional hardcoded fallback (NOT recommended for public repos).
# If env vars / Streamlit secrets are not set, fill these in.
HARDCODED_SUPABASE_URL: str | None = None  # e.g. "https://xxxx.supabase.co"
HARDCODED_SUPABASE_KEY: str | None = None  # use service_role for backend, anon for client-only


class MissingSupabaseCredentials(RuntimeError):
    pass


def _get_secret(name: str) -> str | None:
    """
    Read from environment variables first, then Streamlit secrets (if available).
    This keeps local dev + Streamlit Cloud deployments simple.
    """
    val = os.getenv(name)
    if val:
        return val

    try:
        import streamlit as st  # type: ignore

        # st.secrets behaves like a dict; may raise if not configured.
        return st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:
        return None


def _client() -> Client:
    url = _get_secret("SUPABASE_URL") or HARDCODED_SUPABASE_URL
    key = (
        _get_secret("SUPABASE_SERVICE_ROLE_KEY")
        or _get_secret("SUPABASE_ANON_KEY")
        or HARDCODED_SUPABASE_KEY
    )
    if not url or not key:
        raise MissingSupabaseCredentials(
            "Missing Supabase credentials.\n"
            "- Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (recommended) or SUPABASE_ANON_KEY\n"
            "- OR set HARDCODED_SUPABASE_URL / HARDCODED_SUPABASE_KEY in supabase_db.py"
        )
    return create_client(url, key)


def ensure_schema() -> None:
    """
    Supabase tables are created in the Supabase dashboard/SQL editor.
    Keep this as a no-op so the app can keep calling ensure_schema().
    """


def create_user(username: str, password: str) -> bool:
    username = str(username or "").strip()
    password = str(password or "")
    if not username or not password:
        return False

    try:
        sb = _client()
    except MissingSupabaseCredentials:
        return False

    # Check existence (avoid duplicate insert errors leaking as generic failure).
    existing = (
        sb.table("users")
        .select("id")
        .eq("username", username)
        .limit(1)
        .execute()
    )
    if getattr(existing, "data", None):
        return False

    password_hash = _pwd.hash(password)
    inserted = (
        sb.table("users")
        .insert({"username": username, "password_hash": password_hash})
        .execute()
    )
    return bool(getattr(inserted, "data", None))


def login_user(username: str, password: str):
    username = str(username or "").strip()
    password = str(password or "")
    if not username or not password:
        return None

    try:
        sb = _client()
    except MissingSupabaseCredentials:
        return None
    res = (
        sb.table("users")
        .select("id, username, password_hash")
        .eq("username", username)
        .limit(1)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    if not rows:
        return None

    user = rows[0]
    if not _pwd.verify(password, user.get("password_hash") or ""):
        return None

    return user


def save_submission(username: str, score: float, time_taken_seconds: int, submitted_at: str | None = None) -> bool:
    username = str(username or "").strip()
    if not username:
        return False

    submitted_at = submitted_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        sb = _client()
    except MissingSupabaseCredentials:
        return False
    res = (
        sb.table("test_history")
        .insert(
            {
                "username": username,
                "score": float(score),
                "time_taken_seconds": int(time_taken_seconds),
                "date": submitted_at,
            }
        )
        .execute()
    )
    return bool(getattr(res, "data", None))


def get_history(username: str) -> List[Tuple]:
    username = str(username or "").strip()
    if not username:
        return []

    try:
        sb = _client()
    except MissingSupabaseCredentials:
        return []
    res = (
        sb.table("test_history")
        .select("score,time_taken_seconds,date")
        .eq("username", username)
        .order("id", desc=False)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    return [(r.get("score"), r.get("time_taken_seconds"), r.get("date")) for r in rows]
