from pydantic import BaseModel, Field


class ExtractedJob(BaseModel):
    client_name: str = ""
    site_address: str = ""
    job_description: str = ""
    po_number: str = ""
    contact_name: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    source_references: list[str] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    missing_fields: list[str] = Field(default_factory=list)
    notes: str = ""
