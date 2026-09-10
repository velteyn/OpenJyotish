"""AI Chat thread store — SQLite persistence for shelved conversations.

Owned by the AI Chat tab. The Guru tab owns a parallel store so the two
features diverge freely; only the DB connection helper is shared.
"""

import json
from typing import Any, Dict, List, Optional

from jhora.charts.chart import ChartData
from jhora.core.database import get_db

MAX_THREADS_PER_CHART = 50
TITLE_LENGTH = 40


def chart_fingerprint(cd: ChartData) -> str:
    """Stable identity of the birth chart a thread belongs to.

    Uses the Julian day (full birth moment incl. time) plus rounded place,
    so same-day charts at different times do not share threads.
    """
    return "|".join([
        f"{cd.julian_day:.4f}",
        f"{round(cd.latitude, 4):.4f}",
        f"{round(cd.longitude, 4):.4f}",
        cd.timezone or "",
    ])


def thread_title(messages: List[Dict[str, Any]]) -> str:
    """Human title from the thread's first message (no model call needed)."""
    for m in messages:
        text = str((m or {}).get("content") or "").strip().replace("\n", " ")
        if text:
            if len(text) > TITLE_LENGTH:
                return text[:TITLE_LENGTH] + "..."
            return text
    return "Untitled thread"


def save_thread(chart_fp: str, title: str, payload: Dict[str, list],
                thread_id: Optional[int] = None) -> int:
    """Insert a new thread, or update the resumed one; prunes past the cap.

    payload is {"history": model messages, "transcript": display blocks},
    so resume restores both the model context and the full visible thread
    (including pre-compaction exchanges).
    """
    conn = get_db()
    blob = json.dumps(payload, ensure_ascii=False)
    if thread_id is None:
        cur = conn.execute(
            "INSERT INTO chat_threads (chart_fp, title, updated_at, messages_json)"
            " VALUES (?, ?, datetime('now'), ?)",
            (chart_fp, title, blob))
        thread_id = cur.lastrowid
    else:
        conn.execute(
            "UPDATE chat_threads SET title = ?, updated_at = datetime('now'),"
            " messages_json = ? WHERE id = ?",
            (title, blob, thread_id))
    conn.execute(
        """DELETE FROM chat_threads WHERE chart_fp = ? AND id NOT IN (
               SELECT id FROM chat_threads WHERE chart_fp = ?
               ORDER BY updated_at DESC, id DESC LIMIT ?)""",
        (chart_fp, chart_fp, MAX_THREADS_PER_CHART))
    conn.commit()
    return thread_id


def list_threads(chart_fp: str) -> List[Dict[str, Any]]:
    """Newest-first thread summaries for one chart (no message bodies)."""
    conn = get_db()
    cur = conn.execute(
        "SELECT id, title, updated_at, messages_json FROM chat_threads"
        " WHERE chart_fp = ? ORDER BY updated_at DESC, id DESC",
        (chart_fp,))
    threads = []
    for row in cur.fetchall():
        try:
            payload = json.loads(row["messages_json"])
            history = payload.get("history", []) if isinstance(payload, dict) \
                else payload
            count = len(history)
        except (ValueError, TypeError, AttributeError):
            count = 0
        threads.append({"id": row["id"], "title": row["title"],
                        "updated_at": row["updated_at"],
                        "messages": count})
    return threads


def load_thread(thread_id: int) -> Dict[str, list]:
    """Full payload for resume ({"history", "transcript"}); empty when gone."""
    conn = get_db()
    cur = conn.execute("SELECT messages_json FROM chat_threads WHERE id = ?",
                       (thread_id,))
    row = cur.fetchone()
    if row is None:
        return {"history": [], "transcript": []}
    try:
        payload = json.loads(row["messages_json"])
    except (ValueError, TypeError):
        return {"history": [], "transcript": []}
    if not isinstance(payload, dict):
        return {"history": [], "transcript": []}
    history = payload.get("history", [])
    transcript = payload.get("transcript", [])
    if not isinstance(history, list):
        history = []
    if not isinstance(transcript, list):
        transcript = []
    return {"history": history, "transcript": transcript}


def delete_thread(thread_id: int) -> None:
    conn = get_db()
    conn.execute("DELETE FROM chat_threads WHERE id = ?", (thread_id,))
    conn.commit()
