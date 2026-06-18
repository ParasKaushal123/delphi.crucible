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

    # --- Agent UUIDs ---
    BEAR_AGENT_ID: str = "a95d3851-7837-486c-975f-cc3bf62725d7"
    WATCHER_AGENT_ID: str = "9f9a46c6-fd68-413b-b3e4-7e5bbd91f2ca"
    BULL_AGENT_ID: str = "0b798aec-9962-44b6-88cd-031b463305d4"
    PM_AGENT_ID: str = "80e3bfa5-6653-487f-a160-3c12cc3d1d5b"
    QUANT_AGENT_ID: str = "4ba0a643-3d28-4f2b-8f7d-dd4acefd637e"
    HUMAN_OWNER_ID: str = "c1453114-1160-4f97-9a4d-edb04e5d0905"

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

    # --- Agent Names / Handles ---
    PM_AGENT_NAME: str = "yashwanthreddy0615/pm-agent"
    QUANT_AGENT_NAME: str = "yashwanthreddy0615/quant-agent"
    BULL_AGENT_NAME: str = "yashwanthreddy0615/bull-agent"
    BEAR_AGENT_NAME: str = "yashwanthreddy0615/bear-agent"


settings = Settings()
