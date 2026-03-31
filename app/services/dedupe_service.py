import json
import re

from app.db.drafts_repository import list_dedupe_candidates
from app.schemas.extracted_job import ExtractedJob


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split()) if value else ""


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def find_duplicate_match(extracted: ExtractedJob) -> dict:
    email = (extracted.contact_email or "").strip().lower()
    phone = _normalize_phone(extracted.contact_phone)
    client_name = _normalize_text(extracted.client_name)
    site_address = _normalize_text(extracted.site_address)

    for candidate in list_dedupe_candidates():
        payload = json.loads(candidate["extracted_json"])

        candidate_email = str(payload.get("contact_email", "")).strip().lower()
        if email and candidate_email and email == candidate_email:
            return {
                "dedupe_status": "possible_duplicate",
                "matched_draft_id": candidate["id"],
                "match_reason": "contact_email_match",
            }

        candidate_phone = _normalize_phone(str(payload.get("contact_phone", "")))
        if phone and candidate_phone and phone == candidate_phone:
            return {
                "dedupe_status": "possible_duplicate",
                "matched_draft_id": candidate["id"],
                "match_reason": "contact_phone_match",
            }

        candidate_client_name = _normalize_text(str(payload.get("client_name", "")))
        candidate_site_address = _normalize_text(str(payload.get("site_address", "")))
        if (
            client_name
            and site_address
            and candidate_client_name
            and candidate_site_address
            and client_name == candidate_client_name
            and site_address == candidate_site_address
        ):
            return {
                "dedupe_status": "possible_duplicate",
                "matched_draft_id": candidate["id"],
                "match_reason": "client_name_site_address_match",
            }

    return {
        "dedupe_status": "no_match",
        "matched_draft_id": None,
        "match_reason": "",
    }
