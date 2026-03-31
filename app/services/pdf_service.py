from pathlib import Path

from pypdf import PdfReader


def extract_text_from_attachments(attachment_paths: list[str]) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []

    for path in attachment_paths:
        pdf_path = Path(path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"Attachment file not found: {path}")

        text_parts: list[str] = []
        try:
            reader = PdfReader(path)
            for index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(f"[Page {index}]\n{page_text.strip()}")
        except Exception as exc:
            raise ValueError(f"PDF_PARSE_ERROR: {path}") from exc

        combined_text = "\n\n".join(text_parts).strip()
        if not combined_text:
            combined_text = "[No extractable text found in PDF]"
        sources.append(
            {
                "source": f"attachment:{pdf_path.name}",
                "text": combined_text,
            }
        )

    return sources
