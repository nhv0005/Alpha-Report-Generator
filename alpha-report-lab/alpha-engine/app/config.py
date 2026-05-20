"""Environment configuration for the Alpha Engine."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_FAST_MODEL: str = os.getenv("OPENAI_FAST_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Dynatrace
    DT_ENV_URL: str = os.getenv("DT_ENV_URL", "")
    DT_API_TOKEN: str = os.getenv("DT_API_TOKEN", "")

    # App
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "Alpha Engine")
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.0.0")
    DEPLOYMENT_ENV: str = os.getenv("DEPLOYMENT_ENV", "local-lab")
    PORT: int = int(os.getenv("PORT", os.getenv("ALPHA_ENGINE_PORT", "8000")))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # Debug
    DEBUG_TRACES: bool = _bool("DEBUG_TRACES", False)

    # OpenInference privacy
    HIDE_INPUTS: bool = _bool("OPENINFERENCE_HIDE_INPUTS", False)
    HIDE_OUTPUTS: bool = _bool("OPENINFERENCE_HIDE_OUTPUTS", False)
    HIDE_INPUT_IMAGES: bool = _bool("OPENINFERENCE_HIDE_INPUT_IMAGES", True)
    HIDE_EMBEDDING_VECTORS: bool = _bool("OPENINFERENCE_HIDE_EMBEDDING_VECTORS", True)
    HIDE_LLM_INVOCATION_PARAMETERS: bool = _bool(
        "OPENINFERENCE_HIDE_LLM_INVOCATION_PARAMETERS", False
    )


settings = Settings()
