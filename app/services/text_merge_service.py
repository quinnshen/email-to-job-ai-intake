def merge_intake_text(
    body_text: str,
    attachment_texts: list[dict[str, str]],
    drive_texts: list[str],
) -> str:
    sections: list[str] = []

    sections.append("## EMAIL_BODY")
    sections.append(body_text.strip())

    for item in attachment_texts:
        source = item.get("source", "attachment:unknown")
        text = item.get("text", "").strip()
        if not text:
            continue
        sections.append(f"## {source}")
        sections.append(text)

    for index, text in enumerate(drive_texts, start=1):
        cleaned_text = text.strip()
        if not cleaned_text:
            continue
        sections.append(f"## DRIVE_TEXT:{index}")
        sections.append(cleaned_text)

    return "\n\n".join(sections).strip()
