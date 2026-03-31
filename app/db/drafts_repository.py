import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _get_db_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "data" / "drafts.sqlite"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def init_db() -> None:
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS drafts (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                extracted_json TEXT NOT NULL,
                original_body_text TEXT NOT NULL,
                original_attachment_paths_json TEXT NOT NULL,
                original_drive_texts_json TEXT NOT NULL,
                reviewer_note TEXT NOT NULL,
                downstream_job_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def create_draft(*, extracted: dict, body_text: str, attachment_paths: list[str], drive_texts: list[str]) -> dict:
    draft_id = str(uuid4())
    now = _now_utc_iso()

    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(
            """
            INSERT INTO drafts (
                id, status, extracted_json,
                original_body_text,
                original_attachment_paths_json,
                original_drive_texts_json,
                reviewer_note,
                downstream_job_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft_id,
                "pending_approval",
                _to_json(extracted),
                body_text,
                _to_json(attachment_paths),
                _to_json(drive_texts),
                "",
                None,
                now,
                now,
            ),
        )
        conn.commit()

        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def _row_to_draft_detail(row: sqlite3.Row) -> dict:
    return {
        "draft_id": row["id"],
        "status": row["status"],
        "extracted": json.loads(row["extracted_json"]),
        "body_text": row["original_body_text"],
        "attachment_paths": json.loads(row["original_attachment_paths_json"]),
        "drive_texts": json.loads(row["original_drive_texts_json"]),
        "reviewer_note": row["reviewer_note"],
        "downstream_job_id": row["downstream_job_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_drafts_summary(*, limit: int = 50) -> list[dict]:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, status, extracted_json, created_at, updated_at
            FROM drafts
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        summaries: list[dict] = []
        for r in rows:
            extracted = json.loads(r["extracted_json"])
            client_name = extracted.get("client_name", "") if isinstance(extracted, dict) else ""
            site_address = extracted.get("site_address", "") if isinstance(extracted, dict) else ""
            summaries.append(
                {
                    "draft_id": r["id"],
                    "status": r["status"],
                    "client_name": client_name,
                    "site_address": site_address,
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                }
            )
        return summaries
    finally:
        conn.close()


def get_draft_detail(draft_id: str) -> dict:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            raise FileNotFoundError(f"Draft not found: {draft_id}")
        return _row_to_draft_detail(row)
    finally:
        conn.close()


def approve_draft(*, draft_id: str, extracted: dict, downstream_job_id: str, reviewer_note: str) -> dict:
    now = _now_utc_iso()

    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            UPDATE drafts
            SET status = ?, reviewer_note = ?, downstream_job_id = ?, updated_at = ?
            WHERE id = ?
            """,
            ("approved", reviewer_note, downstream_job_id, now, draft_id),
        )
        conn.commit()

        if cur.rowcount == 0:
            raise FileNotFoundError(f"Draft not found: {draft_id}")

        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            raise FileNotFoundError(f"Draft not found: {draft_id}")
        return _row_to_draft_detail(row)
    finally:
        conn.close()


def reject_draft(*, draft_id: str, reviewer_note: str) -> dict:
    now = _now_utc_iso()

    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            UPDATE drafts
            SET status = ?, reviewer_note = ?, updated_at = ?
            WHERE id = ?
            """,
            ("rejected", reviewer_note, now, draft_id),
        )
        conn.commit()

        if cur.rowcount == 0:
            raise FileNotFoundError(f"Draft not found: {draft_id}")

        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            raise FileNotFoundError(f"Draft not found: {draft_id}")
        return _row_to_draft_detail(row)
    finally:
        conn.close()
