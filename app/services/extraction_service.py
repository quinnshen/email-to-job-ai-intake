from app.schemas.extract_request import ExtractRequest
from app.schemas.extracted_job import ExtractedJob
from app.services.llm_service import extract_structured_fields
from app.services.pdf_service import extract_text_from_attachments
from app.services.text_merge_service import merge_intake_text


STRING_FIELDS = [
    "client_name",
    "site_address",
    "job_description",
    "po_number",
    "contact_name",
    "contact_phone",
    "contact_email",
    "notes",
]


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _normalize_payload(payload: dict) -> dict:
    normalized = dict(payload or {})

    for field in STRING_FIELDS:
        value = normalized.get(field, "")
        normalized[field] = value if isinstance(value, str) else ""

    source_refs = normalized.get("source_references", [])
    normalized["source_references"] = _normalize_string_list(source_refs)

    missing = normalized.get("missing_fields", [])
    normalized["missing_fields"] = _normalize_string_list(missing)

    confidence = normalized.get("confidence", 0.0)
    if isinstance(confidence, (int, float)):
        normalized["confidence"] = float(confidence)
    else:
        normalized["confidence"] = 0.0

    return normalized


def run_extraction(request: ExtractRequest) -> ExtractedJob:
    attachment_texts = extract_text_from_attachments(request.attachment_paths)
    merged_text = merge_intake_text(
        body_text=request.body_text,
        attachment_texts=attachment_texts,
        drive_texts=request.drive_texts,
    )
    payload = extract_structured_fields(merged_text)
    normalized_payload = _normalize_payload(payload)
    return ExtractedJob(**normalized_payload)
