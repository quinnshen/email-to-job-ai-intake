import json
from pathlib import Path

from openai import OpenAI

from app.config import (
    get_dashscope_api_key,
    get_dashscope_base_url,
    get_dashscope_model,
    get_llm_provider,
)


def _load_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "extract_job_fields.txt"
    return prompt_path.read_text(encoding="utf-8")


def extract_structured_fields(merged_text: str) -> dict:
    provider = get_llm_provider()
    if provider != "dashscope":
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    client = OpenAI(
        api_key=get_dashscope_api_key(),
        base_url=get_dashscope_base_url(),
    )
    prompt = _load_prompt()

    response = client.chat.completions.create(
        model=get_dashscope_model(),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": merged_text},
        ],
    )

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise ValueError("Model returned empty content")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Model returned malformed JSON output") from exc
