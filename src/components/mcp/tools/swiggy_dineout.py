"""Swiggy Dineout MCP tools — restaurant discovery and table reservations.

Endpoint: https://mcp.swiggy.com/dineout
Auth: Per-user OAuth token (same Swiggy account).
Used for: "book a table" feature.
"""

import logging
from typing import Any

from src.components.mcp.gateway import gateway
from src.components.mcp.http import get_mcp_client

logger = logging.getLogger(__name__)

DINEOUT_BASE = "https://mcp.swiggy.com/dineout"


def _swiggy_headers(user_token: str) -> dict[str, str]:
    """Build auth headers for Swiggy API calls."""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }


@gateway.tool
async def dineout_search_restaurants(
    query: str,
    latitude: float,
    longitude: float,
    cuisine: str = "",
    guests: int = 2,
    user_token: str = "",
) -> dict[str, Any]:
    """Search for dine-in restaurants on Swiggy Dineout.

    Args:
        query: Search text like "rooftop" or "italian".
        latitude: User's latitude.
        longitude: User's longitude.
        cuisine: Filter by cuisine (optional).
        guests: Number of guests.
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    params: dict[str, Any] = {
        "query": query,
        "lat": latitude,
        "lng": longitude,
        "guests": guests,
    }
    if cuisine:
        params["cuisine"] = cuisine

    response = await client.get(
        f"{DINEOUT_BASE}/api/search/restaurants",
        headers=_swiggy_headers(user_token),
        params=params,
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def dineout_get_availability(
    restaurant_id: str,
    date: str,
    guests: int = 2,
    user_token: str = "",
) -> dict[str, Any]:
    """Check table availability at a Dineout restaurant.

    Args:
        restaurant_id: Dineout restaurant ID.
        date: Date in YYYY-MM-DD format.
        guests: Number of guests.
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.get(
        f"{DINEOUT_BASE}/api/restaurant/{restaurant_id}/availability",
        headers=_swiggy_headers(user_token),
        params={"date": date, "guests": guests},
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def dineout_book_table(
    restaurant_id: str,
    date: str,
    time: str,
    guests: int = 2,
    user_token: str = "",
) -> dict[str, Any]:
    """Book a table at a Dineout restaurant.

    Args:
        restaurant_id: Dineout restaurant ID.
        date: Date in YYYY-MM-DD format.
        time: Time slot like "19:30".
        guests: Number of guests.
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.post(
        f"{DINEOUT_BASE}/api/restaurant/{restaurant_id}/book",
        headers=_swiggy_headers(user_token),
        json={"date": date, "time": time, "guests": guests},
    )
    response.raise_for_status()
    return response.json()
