"""
Centralized configuration — loads from .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Band API ---
    BAND_API_KEY: str = os.getenv("BAND_API_KEY", "")
    BAND_PM_BOT_TOKEN: str = os.getenv("BAND_PM_BOT_TOKEN", "")
    BAND_QUANT_BOT_TOKEN: str = os.getenv("BAND_QUANT_BOT_TOKEN", "")
    BAND_BULL_BOT_TOKEN: str = os.getenv("BAND_BULL_BOT_TOKEN", "")
    BAND_BEAR_BOT_TOKEN: str = os.getenv("BAND_BEAR_BOT_TOKEN", "")

    # --- AI/ML API (PM, Bull, Bear) ---
    AIML_API_KEY: str = os.getenv("AIML_API_KEY", "")
    AIML_MODEL: str = os.getenv("AIML_MODEL", "gpt-4o")
    AIML_BASE_URL: str = "https://api.aimlapi.com/v1"

    # --- Featherless AI (Quant) ---
    FEATHERLESS_API_KEY: str = os.getenv("FEATHERLESS_API_KEY", "")
    FEATHERLESS_MODEL: str = os.getenv("FEATHERLESS_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
    FEATHERLESS_BASE_URL: str = "https://api.featherless.ai/v1"

    # --- Redis ---
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # --- Server ---
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WEBHOOK_BASE_URL: str = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")

    # --- Agent Names ---
    PM_AGENT_NAME: str = "pm-agent"
    QUANT_AGENT_NAME: str = "quant-agent"
    BULL_AGENT_NAME: str = "bull-agent"
    BEAR_AGENT_NAME: str = "bear-agent"


settings = Settings()
