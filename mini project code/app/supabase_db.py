import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

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


def clear_health_data() -> bool:
    """
    Clears all rows from `health_data`.
    PostgREST requires a filter for deletes, so we use a broad `neq` filter.
    """
    try:
        sb = _client()
    except MissingSupabaseCredentials:
        return False

    try:
        res = sb.table("health_data").delete().neq("id", 0).execute()
        _ = res  # silence unused var in some linters
        return True
    except Exception:
        # Fallback in case `id` is not present; try a common timestamp column.
        try:
            sb.table("health_data").delete().neq("timestamp", "0001-01-01").execute()
            return True
        except Exception:
            return False


def fetch_health_summary_and_clear() -> Dict[str, Any]:
    """
    Returns a small summary of `health_data`, then clears the table.

    Expected columns (based on your SQL):
    - stress: numeric/float
    - stress_level: text (e.g. 'low'|'moderate'|'high')
    """
    summary: Dict[str, Any] = {
        "avg_stress": None,
        "moderate_high_count": 0,
        "row_count": 0,
    }

    try:
        sb = _client()
    except MissingSupabaseCredentials:
        return summary

    rows = []
    try:
        res = sb.table("health_data").select("stress,stress_level").execute()
        rows = getattr(res, "data", None) or []
    except Exception:
        rows = []

    stresses: List[float] = []
    mh_count = 0
    for r in rows:
        stress = r.get("stress")
        if stress is not None:
            try:
                stresses.append(float(stress))
            except (TypeError, ValueError):
                pass

        lvl = str(r.get("stress_level") or "").strip().lower()
        if lvl in {"moderate", "high"}:
            mh_count += 1

    summary["row_count"] = len(rows)
    summary["moderate_high_count"] = mh_count
    summary["avg_stress"] = (sum(stresses) / len(stresses)) if stresses else None

    clear_health_data()
    return summary


def clear_questions_table() -> bool:
    """
    Clears all rows from Supabase table `questions` (question timing logs).
    PostgREST requires a filter for deletes, so we use a broad `neq` filter.
    """
    try:
        sb = _client()
    except MissingSupabaseCredentials:
        return False

    try:
        sb.table("questions").delete().neq("id", 0).execute()
        return True
    except Exception:
        # Fallback if `id` column doesn't exist.
        try:
            sb.table("questions").delete().neq("qid", "").execute()
            return True
        except Exception:
            return False


def insert_question_timing(qid: str, st_time: str, en_time: str) -> bool:
    """
    Inserts one question timing row into Supabase table `questions`.
    Expected columns: qid (text), st_time (timestamptz), en_time (timestamptz)
    """
    qid = str(qid or "").strip()
    if not qid:
        return False
    try:
        sb = _client()
    except MissingSupabaseCredentials:
        return False

    res = (
        sb.table("questions")
        .insert({"qid": qid, "st_time": st_time, "en_time": en_time})
        .execute()
    )
    return bool(getattr(res, "data", None))


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


def save_submission(
    username: str,
    score: float,
    time_taken_seconds: int,
    submitted_at: str | None = None,
    test_type: str | None = None,
    stress: float | None = None,
) -> bool:
    username = str(username or "").strip()
    if not username:
        return False

    test_type = str(test_type or "").strip() or "foundation"
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
                "type": test_type,
                **({"stress": float(stress)} if stress is not None else {}),
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
