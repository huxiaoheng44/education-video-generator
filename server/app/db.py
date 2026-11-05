"""Tiny SQLite job store. One serial worker + a few request threads is all we support."""
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

from . import config

_lock = threading.Lock()
_conn = None


def _get() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,
                status      TEXT NOT NULL DEFAULT 'queued',
                style       TEXT,
                image_path  TEXT,
                video_path  TEXT,
                poster_path TEXT,
                error       TEXT,
                created_at  TEXT,
                updated_at  TEXT
            )
            """
        )
        _conn.commit()
    return _conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(style: str) -> str:
    jid = uuid.uuid4().hex
    with _lock:
        _get().execute(
            "INSERT INTO jobs (id, status, style, created_at, updated_at) VALUES (?, 'queued', ?, ?, ?)",
            (jid, style, _now(), _now()),
        )
        _get().commit()
    return jid


def update_image_path(jid: str, image_path: str) -> None:
    with _lock:
        _get().execute(
            "UPDATE jobs SET image_path=?, updated_at=? WHERE id=?", (str(image_path), _now(), jid)
        )
        _get().commit()


def next_queued() -> dict | None:
    with _lock:
        row = _get().execute(
            "SELECT * FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        _get().execute("UPDATE jobs SET status='processing', updated_at=? WHERE id=?", (_now(), row["id"]))
        _get().commit()
        return dict(row)


def set_done(jid: str, video_path, poster_path) -> None:
    with _lock:
        _get().execute(
            "UPDATE jobs SET status='done', video_path=?, poster_path=?, error=NULL, updated_at=? WHERE id=?",
            (str(video_path), str(poster_path), _now(), jid),
        )
        _get().commit()


def set_failed(jid: str, error: str) -> None:
    with _lock:
        _get().execute(
            "UPDATE jobs SET status='failed', error=?, updated_at=? WHERE id=?", (error, _now(), jid)
        )
        _get().commit()


def get_job(jid: str) -> dict | None:
    with _lock:
        row = _get().execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        return dict(row) if row else None
