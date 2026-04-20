"""Swiggy Instamart MCP tools — grocery product search and cart.

Endpoint: https://mcp.swiggy.com/im
Auth: Per-user OAuth token (same Swiggy account as food).
Used for: "cook at home" ingredient costs, grocery price comparison with Zepto.
"""

import logging
from typing import Any

from src.components.mcp.gateway import gateway
from src.components.mcp.http import get_mcp_client

logger = logging.getLogger(__name__)

INSTAMART_BASE = "https://mcp.swiggy.com/im"


def _swiggy_headers(user_token: str) -> dict[str, str]:
    """Build auth headers for Swiggy API calls."""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }


@gateway.tool
async def instamart_search_products(
    query: str,
    category: str = "",
    user_token: str = "",
) -> dict[str, Any]:
    """Search for grocery products on Swiggy Instamart.

    Args:
        query: Product name like "paneer" or "olive oil".
        category: Filter by category (optional).
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    params: dict[str, Any] = {"query": query}
    if category:
        params["category"] = category

    response = await client.get(
        f"{INSTAMART_BASE}/api/search/products",
        headers=_swiggy_headers(user_token),
        params=params,
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def instamart_add_to_cart(
    product_id: str,
    quantity: int = 1,
    user_token: str = "",
) -> dict[str, Any]:
    """Add a product to the Instamart cart.

    Args:
        product_id: Instamart product ID.
        quantity: Number of units.
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.post(
        f"{INSTAMART_BASE}/api/cart/add",
        headers=_swiggy_headers(user_token),
        json={"product_id": product_id, "quantity": quantity},
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def instamart_get_cart(
    user_token: str = "",
) -> dict[str, Any]:
    """Get the current Instamart cart with delivery estimate.

    Args:
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.get(
        f"{INSTAMART_BASE}/api/cart",
        headers=_swiggy_headers(user_token),
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def instamart_apply_offer(
    coupon_code: str,
    user_token: str = "",
) -> dict[str, Any]:
    """Apply a coupon to the Instamart cart.

    Args:
        coupon_code: Coupon code.
        user_token: User's Swiggy OAuth token.
    """
    client = get_mcp_client()
    response = await client.post(
        f"{INSTAMART_BASE}/api/cart/apply-offer",
        headers=_swiggy_headers(user_token),
        json={"coupon_code": coupon_code},
    )
    response.raise_for_status()
    return response.json()
