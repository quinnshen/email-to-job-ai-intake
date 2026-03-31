from fastapi import FastAPI, HTTPException

from app.schemas.extract_request import ExtractRequest
from app.schemas.draft import DraftCreateResponse, DraftDetail, DraftSummary
from app.schemas.draft_review_actions import DraftReviewActionRequest
from app.db.drafts_repository import init_db
from app.services.draft_service import (
    approve_draft,
    extract_and_save_draft,
    get_draft,
    list_drafts,
    reject_draft_action,
)


app = FastAPI(title="Email to Job Intake API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.post("/api/extract", response_model=DraftCreateResponse)
def extract(request: ExtractRequest) -> DraftCreateResponse:
    try:
        return extract_and_save_draft(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        message = str(exc).lower()
        if "json" in message or "model returned" in message:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc


@app.get("/api/drafts", response_model=list[DraftSummary])
def drafts() -> list[DraftSummary]:
    return list_drafts()


@app.get("/api/drafts/{draft_id}", response_model=DraftDetail)
def draft_detail(draft_id: str) -> DraftDetail:
    try:
        return get_draft(draft_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc


@app.post("/api/drafts/{draft_id}/approve", response_model=DraftDetail)
def approve(draft_id: str, review: DraftReviewActionRequest) -> DraftDetail:
    try:
        return approve_draft(draft_id, review)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc


@app.post("/api/drafts/{draft_id}/reject", response_model=DraftDetail)
def reject(draft_id: str, review: DraftReviewActionRequest) -> DraftDetail:
    try:
        return reject_draft_action(draft_id, review)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc
