from fastapi import FastAPI, HTTPException

from app.schemas.extract_request import ExtractRequest
from app.schemas.extracted_job import ExtractedJob
from app.services.extraction_service import run_extraction


app = FastAPI(title="Email to Job Intake API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/extract", response_model=ExtractedJob)
def extract(request: ExtractRequest) -> ExtractedJob:
    try:
        return run_extraction(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        message = str(exc).lower()
        if "json" in message or "model returned" in message:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc
