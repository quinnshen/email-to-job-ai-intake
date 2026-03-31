from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.extracted_job import ExtractedJob

DraftStatus = Literal["pending_approval", "approved", "rejected"]


class DraftCreateResponse(BaseModel):
    draft_id: str
    status: DraftStatus
    extracted: ExtractedJob
    created_at: datetime
    updated_at: datetime


class DraftSummary(BaseModel):
    draft_id: str
    status: DraftStatus
    client_name: str
    site_address: str
    created_at: datetime
    updated_at: datetime


class DraftDetail(BaseModel):
    draft_id: str
    status: DraftStatus
    extracted: ExtractedJob

    body_text: str
    attachment_paths: list[str]
    drive_texts: list[str]

    reviewer_note: str
    downstream_job_id: str | None

    created_at: datetime
    updated_at: datetime
