"""Zepto MCP tools — grocery search, cart, order history.

Endpoint: https://mcp.zepto.co.in/mcp
Auth: Per-user OAuth token (Indian mobile number).
Used for: grocery price comparison with Instamart, "cook at home" ingredient costs.
"""

import logging
from typing import Any

from src.components.mcp.gateway import gateway
from src.components.mcp.http import get_mcp_client

logger = logging.getLogger(__name__)

ZEPTO_BASE = "https://mcp.zepto.co.in"


def _zepto_headers(user_token: str) -> dict[str, str]:
    """Build auth headers for Zepto API calls."""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }


@gateway.tool
async def zepto_search_products(
    query: str,
    category: str = "",
    user_token: str = "",
) -> dict[str, Any]:
    """Search for products on Zepto.

    Args:
        query: Product name like "atta" or "chicken breast".
        category: Filter by category like "fruits", "dairy" (optional).
        user_token: User's Zepto OAuth token.
    """
    client = get_mcp_client()
    params: dict[str, Any] = {"query": query}
    if category:
        params["category"] = category

    response = await client.get(
        f"{ZEPTO_BASE}/api/search/products",
        headers=_zepto_headers(user_token),
        params=params,
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def zepto_add_to_cart(
    product_id: str,
    quantity: int = 1,
    user_token: str = "",
) -> dict[str, Any]:
    """Add a product to the Zepto cart.

    Args:
        product_id: Zepto product ID.
        quantity: Number of units.
        user_token: User's Zepto OAuth token.
    """
    client = get_mcp_client()
    response = await client.post(
        f"{ZEPTO_BASE}/api/cart/add",
        headers=_zepto_headers(user_token),
        json={"product_id": product_id, "quantity": quantity},
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def zepto_get_cart(
    user_token: str = "",
) -> dict[str, Any]:
    """Get the current Zepto cart with delivery time estimate.

    Args:
        user_token: User's Zepto OAuth token.
    """
    client = get_mcp_client()
    response = await client.get(
        f"{ZEPTO_BASE}/api/cart",
        headers=_zepto_headers(user_token),
    )
    response.raise_for_status()
    return response.json()


@gateway.tool
async def zepto_get_order_history(
    user_token: str = "",
) -> dict[str, Any]:
    """Get past Zepto orders. Useful for reordering and tracking spending.

    Args:
        user_token: User's Zepto OAuth token.
    """
    client = get_mcp_client()
    response = await client.get(
        f"{ZEPTO_BASE}/api/orders/history",
        headers=_zepto_headers(user_token),
    )
    response.raise_for_status()
    return response.json()
