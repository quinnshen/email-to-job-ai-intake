# Email-to-Job AI Intake

AI-powered intake automation backend that converts messy email/PDF inputs into structured job drafts with review workflow, deduplication, and failed-state handling.

## Overview

This project is a backend prototype for **operational intake automation**.

It accepts unstructured job request inputs such as:

- email body text
- PDF attachments
- copied document text

and turns them into **structured job drafts** that can move through a reviewable workflow.

Instead of only returning raw LLM output, the system persists workflow state in SQLite and classifies each intake into one of several operational states:

- `pending_approval`
- `manual_review_required`
- `approved`
- `rejected`
- `failed`

This project demonstrates how to build a more realistic AI workflow backend for operations use cases, rather than a one-off extraction demo.

---

## Problem It Solves

Operational requests often arrive in messy formats:

- long emails
- attached PDFs
- copied notes from linked documents
- incomplete or inconsistent information

A basic LLM extraction demo can turn those inputs into JSON, but real workflows need more than that.

This project adds the missing backend workflow pieces:

- structured extraction
- persistence
- review states
- deduplication signals
- failure classification
- downstream action readiness

---

## Current Capabilities

### 1. Structured intake extraction
The system accepts:

- `body_text`
- `attachment_paths`
- `drive_texts`

and extracts a normalized job payload with fields such as:

- `client_name`
- `site_address`
- `job_description`
- `po_number`
- `contact_name`
- `contact_phone`
- `contact_email`
- `source_references`
- `confidence`
- `missing_fields`
- `notes`

### 2. Draft persistence
Each extraction result is saved as a **draft** in SQLite, together with:

- original input payload
- extracted structured output
- workflow status
- review metadata
- dedupe metadata
- failure metadata
- reviewer notes
- mock downstream job id

### 3. Review workflow
Drafts can move through a reviewable workflow:

- `pending_approval`
- `manual_review_required`
- `approved`
- `rejected`
- `failed`

### 4. Rule-based manual review classification
New drafts are classified automatically.

They are sent to `manual_review_required` when:

- key fields are missing
- confidence is below threshold
- deduplication signals a possible duplicate

### 5. Rule-based deduplication
The system performs lightweight dedupe checks using existing non-failed drafts.

Current rules:

- exact `contact_email` match
- normalized `contact_phone` match
- normalized `client_name + site_address` match

### 6. Failed-state handling
When extraction fails in a classified way, the system attempts to persist the intake as a `failed` draft instead of only returning a raw server error.

### 7. Mock downstream job creation
Approved drafts trigger a mock downstream job creation step and receive a generated `downstream_job_id`.

---

## Status Model

### `pending_approval`
The draft is structurally valid and ready for human approval.

Typical conditions:
- key fields present
- confidence above threshold
- no duplicate signal

### `manual_review_required`
The draft needs manual inspection before normal approval.

Typical conditions:
- missing key fields
- low confidence
- possible duplicate detected

### `approved`
The draft has been approved and a mock downstream job has been created.

### `rejected`
The draft has been explicitly rejected by a reviewer.

### `failed`
The draft could not be extracted successfully and was classified as a failed intake.

---

## Architecture

High-level flow:

```text
Input
  -> Text Extraction / Merge
  -> Structured LLM Extraction
  -> Review Classification
  -> Dedupe Check
  -> Draft Persistence (SQLite)
  -> Review Action
  -> Mock Downstream Job Creation
```

More concretely:

```text
email / pdf / drive text
  -> extraction service
  -> extracted job payload
  -> draft service
      -> classify status
      -> dedupe check
      -> persist draft
  -> API response
```

---

## API Endpoints

### `GET /health`
Basic health check.

Response:

```json
{"status": "ok"}
```

### `POST /api/extract`
Creates a new draft from input text/PDF/document content.

Request body:

```json
{
  "body_text": "Hi team, please create a new electrical job for North Shore Facilities at 88 Harbour Road, Neutral Bay NSW. The issue is faulty lighting in the reception area and one damaged fitting needs replacement. PO number is PO-90021. Site contact is Emily Carter, phone 0411 222 333, email emily.carter+demo1@example.com.",
  "attachment_paths": [],
  "drive_texts": []
}
```

Example successful response:

```json
{
  "draft_id": "1b17530e-b47e-4384-8d9b-8eb09b9dd3ce",
  "status": "pending_approval",
  "extracted": {
    "client_name": "North Shore Facilities",
    "site_address": "88 Harbour Road, Neutral Bay NSW",
    "job_description": "Faulty lighting in the reception area and one damaged fitting needs replacement",
    "po_number": "PO-90021",
    "contact_name": "Emily Carter",
    "contact_phone": "0411 222 333",
    "contact_email": "emily.carter+demo1@example.com",
    "source_references": ["EMAIL_BODY"],
    "confidence": 1.0,
    "missing_fields": [],
    "notes": ""
  },
  "dedupe_status": "no_match",
  "matched_draft_id": null,
  "match_reason": "",
  "review_reasons": [],
  "failure_reason": "",
  "created_at": "2026-03-31T07:52:03.266074Z",
  "updated_at": "2026-03-31T07:52:03.266074Z"
}
```

### `GET /api/drafts`
Returns lightweight draft summaries for queue-style listing.

Example response:

```json
[
  {
    "draft_id": "1b17530e-b47e-4384-8d9b-8eb09b9dd3ce",
    "status": "pending_approval",
    "client_name": "North Shore Facilities",
    "site_address": "88 Harbour Road, Neutral Bay NSW",
    "created_at": "2026-03-31T07:52:03.266074Z",
    "updated_at": "2026-03-31T07:52:03.266074Z"
  }
]
```

### `GET /api/drafts/{draft_id}`
Returns full draft detail, including:

- extracted payload
- original request fields
- dedupe metadata
- review metadata
- failure metadata
- reviewer note
- downstream job id

### `POST /api/drafts/{draft_id}/approve`
Approves a draft and creates a mock downstream job.

Allowed only from:

- `pending_approval`

Example request:

```json
{
  "reviewer_note": "Looks good"
}
```

### `POST /api/drafts/{draft_id}/reject`
Rejects a draft.

Allowed from:

- `pending_approval`
- `manual_review_required`

Example request:

```json
{
  "reviewer_note": "Missing details"
}
```

---

## Example Scenarios

### Scenario 1: complete request
Input contains all key fields and no duplicate signal.

Result:
- `status = pending_approval`

### Scenario 2: possible duplicate
Input matches an existing draft by email, phone, or client+address.

Result:
- `status = manual_review_required`
- `dedupe_status = possible_duplicate`

### Scenario 3: missing key field
Input is missing something important such as `site_address`.

Result:
- `status = manual_review_required`
- `review_reasons` includes the missing key field reason

### Scenario 4: malformed attachment / extraction failure
Input cannot be extracted successfully.

Result:
- `status = failed`
- `failure_reason` is populated

---

## Project Structure

```text
app/
├─ db/
│  ├─ __init__.py
│  └─ drafts_repository.py
├─ prompts/
│  └─ extract_job_fields.txt
├─ schemas/
│  ├─ draft.py
│  ├─ draft_review_actions.py
│  ├─ extract_request.py
│  └─ extracted_job.py
├─ services/
│  ├─ dedupe_service.py
│  ├─ draft_service.py
│  ├─ extraction_service.py
│  ├─ llm_service.py
│  ├─ mock_job_service.py
│  ├─ pdf_service.py
│  └─ text_merge_service.py
├─ config.py
└─ main.py
```

---

## Tech Stack

- Python 3.11
- FastAPI
- Pydantic
- SQLite
- pypdf
- python-dotenv
- OpenAI-compatible SDK
- DashScope / Qwen (current local setup)

---

## Local Setup

### 1. Create virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the template:

```bash
cp .env.example .env
```

Example `.env`:

```env
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=your_api_key
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus
APP_ENV=dev
```

Notes:
- exact DashScope base URL may differ by region
- do not commit `.env`

### 3. Start the API

```bash
uvicorn app.main:app --reload
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

---

## Testing Notes

Validated flows include:

- extraction from pure email body
- extraction from PDF input
- extraction from `drive_texts`
- blank input rejection
- missing PDF handling
- approve / reject workflow
- duplicate detection
- manual review classification
- failed draft creation for extraction failures

---

## Current Limitations

This is still a backend prototype.

Not implemented yet:

- OCR for scanned PDFs
- real Tradify integration
- advanced fuzzy deduplication
- authentication / authorization
- frontend review UI
- audit log / observability layer
- production deployment setup

---

## Future Improvements

Potential next steps:

- real downstream adapter for Tradify or similar systems
- OCR support for scanned attachments
- richer reviewer queue / admin UI
- stronger dedupe logic
- audit logs and event history
- retry and replay tooling for failed drafts
- containerization and deployment setup

---

## Security Notes

- `.env` is ignored and should never be committed
- use only sample/test data in this repository
- do not commit real customer data or live credentials

---

## Portfolio Positioning

This project is intended as a portfolio-quality backend prototype for AI workflow automation.

It is designed to show not only extraction quality, but also:

- workflow-aware backend design
- stateful persistence
- reviewability
- failure handling
- operational safety signals such as deduplication

---

## License

For personal portfolio / demo use.
