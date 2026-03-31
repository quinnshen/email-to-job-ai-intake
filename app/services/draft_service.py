from app.db.drafts_repository import (
    approve_draft as approve_draft_repo,
    create_draft,
    get_draft_detail,
    list_drafts_summary,
    reject_draft,
)
from app.schemas.draft import DraftCreateResponse, DraftDetail, DraftSummary
from app.schemas.draft_review_actions import DraftReviewActionRequest
from app.schemas.extract_request import ExtractRequest
from app.services.extraction_service import run_extraction
from app.services.mock_job_service import create_job


def extract_and_save_draft(request: ExtractRequest) -> DraftCreateResponse:
    extracted = run_extraction(request)
    record = create_draft(
        extracted=extracted.model_dump(),
        body_text=request.body_text,
        attachment_paths=request.attachment_paths,
        drive_texts=request.drive_texts,
    )
    return DraftCreateResponse(
        draft_id=record["id"],
        status=record["status"],
        extracted=extracted,
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


def list_drafts() -> list[DraftSummary]:
    summaries = list_drafts_summary()
    return [DraftSummary(**s) for s in summaries]


def get_draft(draft_id: str) -> DraftDetail:
    detail = get_draft_detail(draft_id)
    return DraftDetail(**detail)


def approve_draft(draft_id: str, review: DraftReviewActionRequest) -> DraftDetail:
    current = get_draft_detail(draft_id)
    if current["status"] != "pending_approval":
        raise ValueError("Draft is not in pending_approval state")

    job_id = create_job(extracted=current["extracted"])
    updated = approve_draft_repo(
        draft_id=draft_id,
        extracted=current["extracted"],
        downstream_job_id=job_id,
        reviewer_note=review.reviewer_note,
    )
    return DraftDetail(**updated)


def reject_draft_action(draft_id: str, review: DraftReviewActionRequest) -> DraftDetail:
    current = get_draft_detail(draft_id)
    if current["status"] != "pending_approval":
        raise ValueError("Draft is not in pending_approval state")

    updated = reject_draft(draft_id=draft_id, reviewer_note=review.reviewer_note)
    return DraftDetail(**updated)

