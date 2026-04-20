"""Indian Nutrient Databank (INDB) tools — Indian food nutrition lookup.

Data source: INDB dataset (1,014 Indian recipes with ICMR nutrition data).
Stored in MongoDB collection: `indian_nutrition`.
No external API — local database queries. Free, offline, instant.

The dataset is loaded into MongoDB via a seed script (scripts/seed_indb.py).
"""

import logging
from typing import Any

from src.components.mcp.gateway import gateway
from src.shared import get_db

logger = logging.getLogger(__name__)


def _get_nutrition_collection():  # type: ignore[no-untyped-def] — motor untyped
    """Get the indian_nutrition MongoDB collection."""
    db = get_db()
    return db.indian_nutrition


@gateway.tool
async def indian_food_nutrition(
    food_name: str,
) -> dict[str, Any]:
    """Look up nutrition data for an Indian food item from ICMR database.

    Covers 1,014 common Indian recipes: dal, roti, biryani, dosa, sabzi, etc.
    Returns nutrition per 100g and per serving.

    Args:
        food_name: Indian food name like "dal makhani" or "masala dosa".
    """
    collection = _get_nutrition_collection()

    # Text search for flexible matching (handles "dal" matching "dal makhani")
    result = await collection.find_one(
        {"$text": {"$search": food_name}},
        {"score": {"$meta": "textScore"}},
    )

    if not result:
        # Fallback: regex partial match
        result = await collection.find_one({"name": {"$regex": food_name, "$options": "i"}})

    if not result:
        return {"found": False, "message": f"No nutrition data found for '{food_name}'"}

    return {
        "found": True,
        "name": result.get("name", ""),
        "region": result.get("region", ""),
        "category": result.get("category", ""),
        "serving_size_g": result.get("serving_size_g", 0),
        "per_100g": {
            "calories": result.get("calories_per_100g", 0),
            "protein_g": result.get("protein_per_100g", 0),
            "carbs_g": result.get("carbs_per_100g", 0),
            "fat_g": result.get("fat_per_100g", 0),
            "fiber_g": result.get("fiber_per_100g", 0),
        },
        "per_serving": {
            "calories": result.get("calories_per_serving", 0),
            "protein_g": result.get("protein_per_serving", 0),
            "carbs_g": result.get("carbs_per_serving", 0),
            "fat_g": result.get("fat_per_serving", 0),
            "fiber_g": result.get("fiber_per_serving", 0),
        },
    }


@gateway.tool
async def indian_food_search(
    query: str,
    category: str = "",
    region: str = "",
    max_calories: int = 0,
    high_protein: bool = False,
) -> dict[str, Any]:
    """Search Indian foods by name, category, region, or nutrition filters.

    Args:
        query: Search text like "dal" or "paneer".
        category: Filter like "curry", "bread", "rice", "snack" (optional).
        region: Filter like "north", "south", "bengali", "gujarati" (optional).
        max_calories: Max calories per serving, 0 = no limit (optional).
        high_protein: If true, only return items with >15g protein per serving.
    """
    collection = _get_nutrition_collection()

    filter_query: dict[str, Any] = {}

    if query:
        filter_query["name"] = {"$regex": query, "$options": "i"}
    if category:
        filter_query["category"] = {"$regex": category, "$options": "i"}
    if region:
        filter_query["region"] = {"$regex": region, "$options": "i"}
    if max_calories > 0:
        filter_query["calories_per_serving"] = {"$lte": max_calories}
    if high_protein:
        filter_query["protein_per_serving"] = {"$gte": 15}

    cursor = collection.find(filter_query).limit(10)
    results = []
    async for doc in cursor:
        results.append(
            {
                "name": doc.get("name", ""),
                "region": doc.get("region", ""),
                "category": doc.get("category", ""),
                "calories_per_serving": doc.get("calories_per_serving", 0),
                "protein_per_serving": doc.get("protein_per_serving", 0),
                "serving_size_g": doc.get("serving_size_g", 0),
            }
        )

    return {"count": len(results), "foods": results}
