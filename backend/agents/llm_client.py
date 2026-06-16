"""
LLM inference client — wraps both AI/ML API (PM, Bull, Bear) and Featherless (Quant).
Both expose OpenAI-compatible endpoints, so we use a single function.
"""

import httpx
from config import settings


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    provider: str = "aiml",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Call an LLM via OpenAI-compatible API.

    Args:
        system_prompt: System message setting agent identity
        user_prompt: User message with task/data
        provider: "aiml" for AI/ML API, "featherless" for Featherless AI
        temperature: Sampling temperature
        max_tokens: Max response tokens

    Returns:
        The assistant's response text
    """
    if provider == "featherless":
        api_key = settings.FEATHERLESS_API_KEY
        base_url = settings.FEATHERLESS_BASE_URL
        model = settings.FEATHERLESS_MODEL
    else:
        api_key = settings.AIML_API_KEY
        base_url = settings.AIML_BASE_URL
        model = settings.AIML_MODEL

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
