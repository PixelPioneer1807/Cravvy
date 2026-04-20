"""Swiggy Food MCP tools — restaurant search, menus, cart, delivery fees.

Endpoint: https://mcp.swiggy.com/food
Auth: Per-user OAuth token from Swiggy account connection.
"""

import logging
from typing import Any

from src.components.mcp.gateway import gateway
from src.components.mcp.http import get_mcp_client

logger = logging.getLogger(__name__)

SWIGGY_FOOD_BASE = "https://mcp.swiggy.com/food"


def _swiggy_headers(user_token: str) -> dict[str, str]:
    """Build auth headers for Swiggy API calls."""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }


@gateway.tool
async def swiggy_search_restaurants(
    query: str,
    latitude: float,
    longitude: float,
    cuisine: str = "",
    max_price: int = 0,
    user_token: str = "",
) -> dict[str, Any]:
    """Search for restaurants on Swiggy near a location.

    Args:
        query: Search text like "butter chicken" or "dosa".
        latitude: User's latitude.
        longitude: User's longitude.
        cuisine: Filter by cuisine type (optional).
        max_price: Maximum price per item in ₹ (0 = no limit).
        user_token: User's Swiggy OAuth token.
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
        f"{SWIGGY_FOOD_BASE}/api/search/restaurants",
        headers=_swiggy_headers(user_token),
        params=params,
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def swiggy_get_menu(
    restaurant_id: str,
    user_token: str = "",
) -> dict[str, Any]:
    """Get the full menu for a Swiggy restaurant.

    Args:
        restaurant_id: Swiggy restaurant ID.
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.get(
        f"{SWIGGY_FOOD_BASE}/api/restaurant/{restaurant_id}/menu",
        headers=_swiggy_headers(user_token),
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def swiggy_add_to_cart(
    restaurant_id: str,
    item_id: str,
    quantity: int = 1,
    user_token: str = "",
) -> dict[str, Any]:
    """Add an item to the Swiggy cart.

    Args:
        restaurant_id: Swiggy restaurant ID.
        item_id: Menu item ID.
        quantity: Number of items.
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.post(
        f"{SWIGGY_FOOD_BASE}/api/cart/add",
        headers=_swiggy_headers(user_token),
        json={
            "restaurant_id": restaurant_id,
            "item_id": item_id,
            "quantity": quantity,
        },
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def swiggy_get_cart(
    user_token: str = "",
) -> dict[str, Any]:
    """Get the current Swiggy cart contents, totals, and fees.

    Args:
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.get(
        f"{SWIGGY_FOOD_BASE}/api/cart",
        headers=_swiggy_headers(user_token),
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def swiggy_apply_offer(
    coupon_code: str,
    user_token: str = "",
) -> dict[str, Any]:
    """Apply a coupon or offer to the Swiggy cart.

    Args:
        coupon_code: The coupon/offer code.
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.post(
        f"{SWIGGY_FOOD_BASE}/api/cart/apply-offer",
        headers=_swiggy_headers(user_token),
        json={"coupon_code": coupon_code},
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def swiggy_get_delivery_fee(
    restaurant_id: str,
    latitude: float,
    longitude: float,
    user_token: str = "",
) -> dict[str, Any]:
    """Get delivery fee and tax estimate for a Swiggy restaurant.

    Args:
        restaurant_id: Swiggy restaurant ID.
        latitude: Delivery address latitude.
        longitude: Delivery address longitude.
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.get(
        f"{SWIGGY_FOOD_BASE}/api/restaurant/{restaurant_id}/delivery-fee",
        headers=_swiggy_headers(user_token),
        params={"lat": latitude, "lng": longitude},
    )
    response.raise_for_status()
    return response.json()
