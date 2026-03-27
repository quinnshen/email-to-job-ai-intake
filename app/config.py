import os

from dotenv import load_dotenv


load_dotenv()


def get_llm_provider() -> str:
    return os.getenv("LLM_PROVIDER", "dashscope").strip().lower() or "dashscope"


def get_dashscope_api_key() -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY is required")
    return api_key


def get_dashscope_base_url() -> str:
    return (
        os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").strip()
        or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )


def get_dashscope_model() -> str:
    return os.getenv("DASHSCOPE_MODEL", "qwen-plus").strip() or "qwen-plus"
