from pydantic import BaseModel, Field


class DraftReviewActionRequest(BaseModel):
    reviewer_note: str = Field(default="")
