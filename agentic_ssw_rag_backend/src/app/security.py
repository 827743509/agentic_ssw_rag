from fastapi import Header, HTTPException

from .config import get_settings


async def verify_api_key(x_api_key: str | None = Header(default=None)):
    settings = get_settings()
    if not settings.enable_api_key:
        return

    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
