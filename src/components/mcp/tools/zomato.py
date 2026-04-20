"""Zomato MCP tools — restaurant search, menus, cart management.

All tools require a user_token (OAuth) obtained when the user
connects their Zomato account in the integrations module.
Endpoint: https://mcp-server.zomato.com
"""

import logging
from typing import Any

from src.components.mcp.gateway import gateway
from src.components.mcp.http import get_mcp_client

logger = logging.getLogger(__name__)

ZOMATO_BASE = "https://mcp-server.zomato.com"


def _zomato_headers(user_token: str) -> dict[str, str]:
    """Build auth headers for Zomato API calls."""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }


@gateway.tool
async def zomato_search_restaurants(
    query: str,
    latitude: float,
    longitude: float,
    cuisine: str = "",
    max_price: int = 0,
    user_token: str = "",
) -> dict[str, Any]:
    """Search for restaurants on Zomato near a location.

    Args:
        query: Search text like "biryani" or "pizza".
        latitude: User's latitude.
        longitude: User's longitude.
        cuisine: Filter by cuisine type (optional).
        max_price: Maximum price per item in ₹ (0 = no limit).
        user_token: User's Zomato OAuth token.
    """
    client = get_mcp_client()
    params: dict[str, Any] = {
        "query": query,
        "lat": latitude,
        "lng": longitude,
    }
    if cuisine:
        params["cuisine"] = cuisine
    if max_price > 0:
        params["max_price"] = max_price

    response = await client.get(
        f"{ZOMATO_BASE}/api/search/restaurants",
        headers=_zomato_headers(user_token),
        params=params,
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def zomato_get_menu(
    restaurant_id: str,
    user_token: str = "",
) -> dict[str, Any]:
    """Get the full menu for a Zomato restaurant.

    Args:
        restaurant_id: Zomato restaurant ID.
        user_token: User's Zomato OAuth token.
    """
    client = get_mcp_client()
    response = await client.get(
        f"{ZOMATO_BASE}/api/restaurant/{restaurant_id}/menu",
        headers=_zomato_headers(user_token),
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def zomato_add_to_cart(
    restaurant_id: str,
    item_id: str,
    quantity: int = 1,
    customizations: str = "",
    user_token: str = "",
) -> dict[str, Any]:
    """Add an item to the Zomato cart.

    Args:
        restaurant_id: Zomato restaurant ID.
        item_id: Menu item ID.
        quantity: Number of items to add.
        customizations: Any customization notes.
        user_token: User's Zomato OAuth token.
    """
    client = get_mcp_client()
    body: dict[str, Any] = {
        "restaurant_id": restaurant_id,
        "item_id": item_id,
        "quantity": quantity,
    }
    if customizations:
        body["customizations"] = customizations

    response = await client.post(
        f"{ZOMATO_BASE}/api/cart/add",
        headers=_zomato_headers(user_token),
        json=body,
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def zomato_get_cart(
    user_token: str = "",
) -> dict[str, Any]:
    """Get the current Zomato cart contents, totals, and fees.

    Args:
        user_token: User's Zomato OAuth token.
    """
    client = get_mcp_client()
    response = await client.get(
        f"{ZOMATO_BASE}/api/cart",
        headers=_zomato_headers(user_token),
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def zomato_apply_offer(
    coupon_code: str,
    user_token: str = "",
) -> dict[str, Any]:
    """Apply a coupon or offer to the Zomato cart.

    Args:
        coupon_code: The coupon/offer code to apply.
        user_token: User's Zomato OAuth token.
    """
    client = get_mcp_client()
    response = await client.post(
        f"{ZOMATO_BASE}/api/cart/apply-offer",
        headers=_zomato_headers(user_token),
        json={"coupon_code": coupon_code},
    )
    response.raise_for_status()
    return response.json()
