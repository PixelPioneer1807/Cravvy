"""Google Maps MCP tools — nearby places, restaurant search, directions.

Endpoint: https://maps.googleapis.com/maps/api
Auth: Server API key (GOOGLE_MAPS_API_KEY) — NOT per-user.
Free: $200/month credit (~28K place searches or ~40K geocodes).
"""

import logging
from typing import Any

from src.components.mcp.gateway import gateway
from src.components.mcp.http import get_mcp_client
from src.shared import settings

logger = logging.getLogger(__name__)

MAPS_BASE = "https://maps.googleapis.com/maps/api"


def _maps_params() -> dict[str, str]:
    """Base params with API key."""
    return {"key": settings.GOOGLE_MAPS_API_KEY}


@gateway.tool
async def maps_search_nearby(
    latitude: float,
    longitude: float,
    radius: int = 2000,
    place_type: str = "restaurant",
    keyword: str = "",
) -> dict[str, Any]:
    """Find places near a location (restaurants, grocery stores, cafes).

    Args:
        latitude: Center latitude.
        longitude: Center longitude.
        radius: Search radius in meters (default 2000 = 2km).
        place_type: Type like "restaurant", "grocery_or_supermarket", "cafe".
        keyword: Filter keyword like "biryani" or "organic" (optional).
    """
    client = get_mcp_client()
    params: dict[str, Any] = {
        **_maps_params(),
        "location": f"{latitude},{longitude}",
        "radius": radius,
        "type": place_type,
    }
    if keyword:
        params["keyword"] = keyword

    response = await client.get(f"{MAPS_BASE}/place/nearbysearch/json", params=params)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    places = []
    for place in results[:10]:
        places.append(
            {
                "place_id": place.get("place_id", ""),
                "name": place.get("name", ""),
                "address": place.get("vicinity", ""),
                "rating": place.get("rating", 0),
                "total_ratings": place.get("user_ratings_total", 0),
                "open_now": place.get("opening_hours", {}).get("open_now"),
                "price_level": place.get("price_level"),
                "types": place.get("types", []),
                "location": place.get("geometry", {}).get("location", {}),
            }
        )

    return {"count": len(places), "places": places}


@gateway.tool
async def maps_search_places(
    query: str,
    latitude: float = 0,
    longitude: float = 0,
    radius: int = 5000,
) -> dict[str, Any]:
    """Search for places by text query (more flexible than nearby search).

    Args:
        query: Free text like "best biryani in Koramangala" or "grocery store near me".
        latitude: Optional center latitude for location bias.
        longitude: Optional center longitude.
        radius: Search radius in meters (optional).
    """
    client = get_mcp_client()
    params: dict[str, Any] = {**_maps_params(), "query": query}

    if latitude and longitude:
        params["location"] = f"{latitude},{longitude}"
        params["radius"] = radius

    response = await client.get(f"{MAPS_BASE}/place/textsearch/json", params=params)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    places = []
    for place in results[:10]:
        places.append(
            {
                "place_id": place.get("place_id", ""),
                "name": place.get("name", ""),
                "address": place.get("formatted_address", ""),
                "rating": place.get("rating", 0),
                "total_ratings": place.get("user_ratings_total", 0),
                "open_now": place.get("opening_hours", {}).get("open_now"),
                "price_level": place.get("price_level"),
                "location": place.get("geometry", {}).get("location", {}),
            }
        )

    return {"count": len(places), "places": places}


@gateway.tool
async def maps_get_place_details(
    place_id: str,
) -> dict[str, Any]:
    """Get detailed info about a specific place.

    Args:
        place_id: Google Maps place ID (from search results).
    """
    client = get_mcp_client()
    params: dict[str, Any] = {
        **_maps_params(),
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,rating,"
        "user_ratings_total,opening_hours,website,price_level,"
        "reviews,geometry",
    }

    response = await client.get(f"{MAPS_BASE}/place/details/json", params=params)
    response.raise_for_status()

    result = response.json().get("result", {})

    return {
        "name": result.get("name", ""),
        "address": result.get("formatted_address", ""),
        "phone": result.get("formatted_phone_number", ""),
        "rating": result.get("rating", 0),
        "total_ratings": result.get("user_ratings_total", 0),
        "website": result.get("website", ""),
        "price_level": result.get("price_level"),
        "hours": result.get("opening_hours", {}).get("weekday_text", []),
        "open_now": result.get("opening_hours", {}).get("open_now"),
        "location": result.get("geometry", {}).get("location", {}),
        "reviews": [
            {
                "author": r.get("author_name", ""),
                "rating": r.get("rating", 0),
                "text": r.get("text", "")[:200],
                "time": r.get("relative_time_description", ""),
            }
            for r in result.get("reviews", [])[:5]
        ],
    }


@gateway.tool
async def maps_get_directions(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    mode: str = "driving",
) -> dict[str, Any]:
    """Get directions and travel time between two points.

    Args:
        origin_lat: Starting latitude.
        origin_lng: Starting longitude.
        dest_lat: Destination latitude.
        dest_lng: Destination longitude.
        mode: Travel mode — "driving", "walking", "transit" (default: driving).
    """
    client = get_mcp_client()
    params: dict[str, Any] = {
        **_maps_params(),
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{dest_lat},{dest_lng}",
        "mode": mode,
    }

    response = await client.get(f"{MAPS_BASE}/directions/json", params=params)
    response.raise_for_status()

    data = response.json()
    routes = data.get("routes", [])

    if not routes:
        return {"found": False, "message": "No route found"}

    leg = routes[0].get("legs", [{}])[0]

    return {
        "found": True,
        "distance": leg.get("distance", {}).get("text", ""),
        "duration": leg.get("duration", {}).get("text", ""),
        "start_address": leg.get("start_address", ""),
        "end_address": leg.get("end_address", ""),
    }


@gateway.tool
async def maps_geocode(
    address: str,
) -> dict[str, Any]:
    """Convert an address to latitude/longitude coordinates.

    Args:
        address: Full or partial address like "Koramangala, Bangalore".
    """
    client = get_mcp_client()
    params: dict[str, Any] = {**_maps_params(), "address": address}

    response = await client.get(f"{MAPS_BASE}/geocode/json", params=params)
    response.raise_for_status()

    results = response.json().get("results", [])

    if not results:
        return {"found": False, "message": f"Could not geocode '{address}'"}

    location = results[0].get("geometry", {}).get("location", {})

    return {
        "found": True,
        "formatted_address": results[0].get("formatted_address", ""),
        "latitude": location.get("lat", 0),
        "longitude": location.get("lng", 0),
    }
