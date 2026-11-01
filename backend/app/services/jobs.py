"""Analysis jobs stored in SQLite and processed one at a time in a background thread.

The app uploads a recording (POST /jobs) and polls GET /jobs/{id}. Because job state lives in
SQLite, the app can be closed and reopened and still pick up the result. Jobs that were queued
or running when the server stopped are marked "interrupted" so the app knows to re-upload.
"""
import json
import logging
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.services.analysis.pipeline import AnalysisError, run_analysis
from app.services.content import get_article

log = logging.getLogger(__name__)

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="analysis")


def init():
    global _conn
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(settings.JOBS_DB, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    with _lock:
        _conn.executescript("""
            PRAGMA journal_mode = WAL;
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                client_ref TEXT,
                topic_id TEXT NOT NULL,
                status TEXT NOT NULL,
                step TEXT,
                progress REAL NOT NULL DEFAULT 0,
                result TEXT,
                error_code TEXT,
                error_message TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS jobs_client_ref_idx ON jobs(client_ref);
        """)
        _conn.execute(
            "UPDATE jobs SET status = 'failed', error_code = 'interrupted', "
            "error_message = 'The server restarted before this analysis finished.', updated_at = ? "
            "WHERE status IN ('queued', 'running')",
            (time.time(),),
        )
        _conn.commit()


def _json_default(o):
    """Analysis code returns NumPy scalars in places (e.g. np.bool_); store them as plain values."""
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def _update(job_id: str, **fields):
    fields["updated_at"] = time.time()
    cols = ", ".join(f"{k} = ?" for k in fields)
    with _lock:
        _conn.execute(f"UPDATE jobs SET {cols} WHERE id = ?", (*fields.values(), job_id))
        _conn.commit()


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "status": row["status"],
        "step": row["step"],
        "progress": row["progress"],
        "topic_id": row["topic_id"],
        "error": {"code": row["error_code"], "message": row["error_message"]} if row["error_code"] else None,
        "result": json.loads(row["result"]) if row["result"] else None,
    }


def get(job_id: str) -> dict | None:
    with _lock:
        row = _conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_dict(row)


def find_active_by_client_ref(client_ref: str) -> dict | None:
    """An earlier upload of the same recording that hasn't failed (lets the app retry safely)."""
    with _lock:
        row = _conn.execute(
            "SELECT * FROM jobs WHERE client_ref = ? AND status != 'failed' ORDER BY created_at DESC LIMIT 1",
            (client_ref,),
        ).fetchone()
    return _row_to_dict(row)


def new_upload_path() -> tuple[str, Path]:
    job_id = uuid.uuid4().hex
    return job_id, settings.UPLOAD_DIR / f"{job_id}.video"


def submit(job_id: str, upload: Path, topic_id: str, first_name: str | None, client_ref: str | None) -> dict:
    now = time.time()
    with _lock:
        _conn.execute(
            "INSERT INTO jobs (id, client_ref, topic_id, status, step, progress, created_at, updated_at) "
            "VALUES (?, ?, ?, 'queued', 'queued', 0, ?, ?)",
            (job_id, client_ref, topic_id, now, now),
        )
        _conn.commit()
    _executor.submit(_run, job_id, upload, topic_id, first_name)
    return get(job_id)


def _run(job_id: str, upload: Path, topic_id: str, first_name: str | None):
    started = time.time()
    _update(job_id, status="running", step="preparing", progress=0.02)
    try:
        article = get_article(topic_id)
        report = run_analysis(str(upload), article, first_name,
                              progress=lambda step, pct: _update(job_id, step=step, progress=pct))
        _update(job_id, status="done", step="done", progress=1.0, result=json.dumps(report, default=_json_default))
        log.info("Job %s done in %.1fs (asr=%s)", job_id, time.time() - started, report["providers"]["asr"])
    except AnalysisError as exc:
        _update(job_id, status="failed", error_code=exc.code, error_message=exc.message)
        log.warning("Job %s failed: %s", job_id, exc.code)
    except Exception:
        log.exception("Job %s crashed", job_id)
        _update(job_id, status="failed", error_code="internal",
                error_message="Something went wrong while analysing your talk. Please try again.")
    finally:
        upload.unlink(missing_ok=True)   # recordings are not kept on the server
