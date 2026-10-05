"""
Geocoding service using OpenStreetMap Nominatim.
Results are cached in-memory with a 24-hour TTL to avoid hammering the API.
"""
import time
from typing import Optional, Tuple
import httpx
from app.core.config import settings

# Simple in-memory cache: {query: (lat, lng, timestamp)}
_CACHE: dict = {}
_TTL_SECONDS = 86400  # 24 hours


async def geocode(address: str) -> Optional[Tuple[float, float]]:
    """
    Returns (lat, lng) for the given address string, or None on failure.
    Uses OSM Nominatim with a respectful User-Agent.
    """
    query = address.strip().lower()
    now = time.time()

    # Check cache
    if query in _CACHE:
        lat, lng, ts = _CACHE[query]
        if now - ts < _TTL_SECONDS:
            return lat, lng

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": settings.USER_AGENT}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return None

    if not data:
        return None

    lat = float(data[0]["lat"])
    lng = float(data[0]["lon"])
    _CACHE[query] = (lat, lng, now)
    return lat, lng
