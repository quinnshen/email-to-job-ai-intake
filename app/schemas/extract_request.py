from pydantic import BaseModel, Field
from pydantic import field_validator


class ExtractRequest(BaseModel):
    body_text: str = Field(..., min_length=1)
    attachment_paths: list[str] = Field(default_factory=list)
    drive_texts: list[str] = Field(default_factory=list)

    @field_validator("body_text")
    @classmethod
    def body_text_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("body_text cannot be blank")
        return stripped
