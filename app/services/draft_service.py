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
from app.schemas.extracted_job import ExtractedJob
from app.services.dedupe_service import find_duplicate_match
from app.services.extraction_service import ExtractionFailureError, run_extraction
from app.services.mock_job_service import create_job

REVIEW_CONFIDENCE_THRESHOLD = 0.75
KEY_FIELDS = ("client_name", "site_address", "job_description")


def _build_review_reasons(extracted: ExtractedJob, dedupe: dict) -> list[str]:
    reasons: list[str] = []

    for field_name in KEY_FIELDS:
        value = getattr(extracted, field_name, "").strip()
        if not value:
            reasons.append(f"missing_{field_name}")

    if extracted.confidence < REVIEW_CONFIDENCE_THRESHOLD:
        reasons.append("low_confidence")

    if dedupe["dedupe_status"] == "possible_duplicate":
        reasons.append("possible_duplicate")

    return reasons


def extract_and_save_draft(request: ExtractRequest) -> DraftCreateResponse:
    try:
        extracted = run_extraction(request)
    except ExtractionFailureError as exc:
        failed_extracted = ExtractedJob()
        try:
            record = create_draft(
                extracted=failed_extracted.model_dump(),
                body_text=request.body_text,
                attachment_paths=request.attachment_paths,
                drive_texts=request.drive_texts,
                status="failed",
                failure_reason=exc.failure_reason,
            )
        except Exception:
            raise exc

        return DraftCreateResponse(
            draft_id=record["draft_id"],
            status=record["status"],
            extracted=failed_extracted,
            dedupe_status=record["dedupe_status"],
            matched_draft_id=record["matched_draft_id"],
            match_reason=record["match_reason"],
            review_reasons=[],
            failure_reason=record["failure_reason"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )

    dedupe = find_duplicate_match(extracted)
    review_reasons = _build_review_reasons(extracted, dedupe)
    status = "pending_approval" if not review_reasons else "manual_review_required"

    record = create_draft(
        extracted=extracted.model_dump(),
        body_text=request.body_text,
        attachment_paths=request.attachment_paths,
        drive_texts=request.drive_texts,
        status=status,
        dedupe_status=dedupe["dedupe_status"],
        matched_draft_id=dedupe["matched_draft_id"],
        match_reason=dedupe["match_reason"],
        review_reasons=review_reasons,
        failure_reason="",
    )
    return DraftCreateResponse(
        draft_id=record["draft_id"],
        status=record["status"],
        extracted=extracted,
        dedupe_status=record["dedupe_status"],
        matched_draft_id=record["matched_draft_id"],
        match_reason=record["match_reason"],
        review_reasons=record["review_reasons"],
        failure_reason=record["failure_reason"],
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
    if current["status"] not in {"pending_approval", "manual_review_required"}:
        raise ValueError("Draft is not in a rejectable state")

    updated = reject_draft(draft_id=draft_id, reviewer_note=review.reviewer_note)
    return DraftDetail(**updated)
