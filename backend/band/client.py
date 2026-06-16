"""
Band REST API client — wrapper for room management, messaging, and member invites.
"""

import httpx
from typing import Optional
from config import settings


class BandClient:
    """
    Wraps the Band Developer API.
    Docs: https://developers.band.us/develop/guide/api
    """

    BASE_URL = "https://openapi.band.us/v2.1"

    def __init__(self, access_token: str = ""):
        self.access_token = access_token or settings.BAND_API_KEY
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._client.aclose()

    def _params(self, **kwargs) -> dict:
        """Inject access_token into every request."""
        return {"access_token": self.access_token, **kwargs}

    # ─── Bands (Rooms) ──────────────────────────────────────

    async def get_bands(self) -> list[dict]:
        """List all bands the bot is a member of."""
        resp = await self._client.get(
            f"{self.BASE_URL}/bands",
            params=self._params(),
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("result_data", {}).get("bands", [])

    async def get_band_info(self, band_key: str) -> dict:
        """Get detailed info about a specific band."""
        resp = await self._client.get(
            f"{self.BASE_URL}/band",
            params=self._params(band_key=band_key),
        )
        resp.raise_for_status()
        return resp.json().get("result_data", {})

    # ─── Posts (Messages) ────────────────────────────────────

    async def send_message(self, band_key: str, content: str) -> dict:
        """Send a message (post) to a band."""
        resp = await self._client.post(
            f"{self.BASE_URL}/band/post/create",
            params=self._params(),
            data={
                "band_key": band_key,
                "content": content,
                "do_push": "true",
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def get_posts(self, band_key: str, locale: str = "en_US") -> list[dict]:
        """Get recent posts from a band."""
        resp = await self._client.get(
            f"{self.BASE_URL}/band/posts",
            params=self._params(band_key=band_key, locale=locale),
        )
        resp.raise_for_status()
        return resp.json().get("result_data", {}).get("items", [])

    async def send_comment(self, band_key: str, post_key: str, body: str) -> dict:
        """Add a comment to an existing post."""
        resp = await self._client.post(
            f"{self.BASE_URL}/band/post/comment/create",
            params=self._params(),
            data={
                "band_key": band_key,
                "post_key": post_key,
                "body": body,
            },
        )
        resp.raise_for_status()
        return resp.json()

    # ─── Convenience Wrappers ────────────────────────────────

    async def send_as_agent(self, band_key: str, agent_name: str, content: str) -> dict:
        """
        Send a message prefixed with the agent identity.
        Band doesn't let us impersonate, so we prefix messages.
        """
        formatted = f"🤖 @{agent_name}:\n{content}"
        return await self.send_message(band_key, formatted)


# ─── Agent-specific clients ──────────────────────────────────

def get_pm_client() -> BandClient:
    return BandClient(access_token=settings.BAND_PM_BOT_TOKEN)


def get_quant_client() -> BandClient:
    return BandClient(access_token=settings.BAND_QUANT_BOT_TOKEN)


def get_bull_client() -> BandClient:
    return BandClient(access_token=settings.BAND_BULL_BOT_TOKEN)


def get_bear_client() -> BandClient:
    return BandClient(access_token=settings.BAND_BEAR_BOT_TOKEN)
