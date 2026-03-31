from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.extracted_job import ExtractedJob

DraftStatus = Literal["pending_approval", "manual_review_required", "approved", "rejected", "failed"]
class DraftCreateResponse(BaseModel):
    draft_id: str
    status: DraftStatus
    extracted: ExtractedJob
    dedupe_status: str = ""
    matched_draft_id: str | None = None
    match_reason: str = ""
    review_reasons: list[str] = Field(default_factory=list)
    failure_reason: str = ""
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
    dedupe_status: str = ""
    matched_draft_id: str | None = None
    match_reason: str = ""
    review_reasons: list[str] = Field(default_factory=list)
    failure_reason: str = ""

    body_text: str
    attachment_paths: list[str]
    drive_texts: list[str]

    reviewer_note: str
    downstream_job_id: str | None

    created_at: datetime
    updated_at: datetime
