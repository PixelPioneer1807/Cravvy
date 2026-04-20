"""Edamam MCP tools — recipe search and nutrition analysis.

Endpoint: https://api.edamam.com
Auth: Server API key (app_id + app_key) — NOT per-user.
2.3M recipes, better Indian food coverage than Spoonacular.
"""

import logging
from typing import Any

from src.components.mcp.gateway import gateway
from src.components.mcp.http import get_mcp_client
from src.shared import settings

logger = logging.getLogger(__name__)

EDAMAM_RECIPE_BASE = "https://api.edamam.com/api/recipes/v2"
EDAMAM_NUTRITION_BASE = "https://api.edamam.com/api/nutrition-details"


def _edamam_params() -> dict[str, str]:
    """Base auth params for Edamam API calls."""
    return {
        "app_id": settings.EDAMAM_APP_ID,
        "app_key": settings.EDAMAM_APP_KEY,
        "type": "public",
    }


@gateway.tool
async def recipe_search(
    query: str,
    cuisine: str = "",
    diet: str = "",
    health: str = "",
    max_calories: int = 0,
    max_time: int = 0,
) -> dict[str, Any]:
    """Search for recipes using Edamam's 2.3M recipe database.

    Args:
        query: Search text like "paneer tikka" or "chicken curry".
        cuisine: Cuisine type like "Indian", "Italian", "Chinese" (optional).
        diet: Diet filter like "balanced", "high-protein", "low-carb" (optional).
        health: Health filter like "vegetarian", "vegan", "gluten-free" (optional).
        max_calories: Maximum calories per serving, 0 = no limit (optional).
        max_time: Maximum cooking time in minutes, 0 = no limit (optional).
    """
    client = get_mcp_client()
    params: dict[str, Any] = {**_edamam_params(), "q": query}

    if cuisine:
        params["cuisineType"] = cuisine
    if diet:
        params["diet"] = diet
    if health:
        params["health"] = health
    if max_calories > 0:
        params["calories"] = f"0-{max_calories}"
    if max_time > 0:
        params["time"] = f"0-{max_time}"

    response = await client.get(EDAMAM_RECIPE_BASE, params=params)
    response.raise_for_status()

    data = response.json()
    hits = data.get("hits", [])

    # Simplify the response — Edamam returns a lot of nested data
    recipes = []
    for hit in hits[:10]:  # limit to 10 results
        recipe = hit.get("recipe", {})
        recipes.append(
            {
                "label": recipe.get("label", ""),
                "image": recipe.get("image", ""),
                "source": recipe.get("source", ""),
                "url": recipe.get("url", ""),
                "servings": recipe.get("yield", 0),
                "cook_time": recipe.get("totalTime", 0),
                "calories_per_serving": round(
                    recipe.get("calories", 0) / max(recipe.get("yield", 1), 1)
                ),
                "cuisine_type": recipe.get("cuisineType", []),
                "diet_labels": recipe.get("dietLabels", []),
                "health_labels": recipe.get("healthLabels", []),
                "ingredients": [ing.get("text", "") for ing in recipe.get("ingredientLines", [])],
                "nutrients": {
                    "calories": round(recipe.get("calories", 0)),
                    "protein": round(
                        recipe.get("totalNutrients", {}).get("PROCNT", {}).get("quantity", 0)
                    ),
                    "carbs": round(
                        recipe.get("totalNutrients", {}).get("CHOCDF", {}).get("quantity", 0)
                    ),
                    "fat": round(
                        recipe.get("totalNutrients", {}).get("FAT", {}).get("quantity", 0)
                    ),
                    "fiber": round(
                        recipe.get("totalNutrients", {}).get("FIBTG", {}).get("quantity", 0)
                    ),
                },
            }
        )

    return {"count": data.get("count", 0), "recipes": recipes}


@gateway.tool
async def recipe_by_ingredients(
    ingredients: str,
    diet: str = "",
    health: str = "",
) -> dict[str, Any]:
    """Find recipes using available ingredients.

    Args:
        ingredients: Comma-separated ingredients like "chicken, rice, tomato".
        diet: Diet filter (optional).
        health: Health filter (optional).
    """
    return await recipe_search(query=ingredients, diet=diet, health=health)


@gateway.tool
async def nutrition_analysis(
    ingredient_list: str,
) -> dict[str, Any]:
    """Analyze nutrition for a list of ingredients.

    Args:
        ingredient_list: Newline-separated ingredients with quantities.
            Example: "200g chicken breast\\n1 cup rice\\n2 tbsp olive oil"
    """
    client = get_mcp_client()
    params = {
        "app_id": settings.EDAMAM_APP_ID,
        "app_key": settings.EDAMAM_APP_KEY,
    }
    body = {
        "ingr": ingredient_list.split("\n"),
    }

    response = await client.post(
        EDAMAM_NUTRITION_BASE,
        params=params,
        json=body,
    )
    response.raise_for_status()

    data = response.json()
    nutrients = data.get("totalNutrients", {})

    return {
        "calories": round(nutrients.get("ENERC_KCAL", {}).get("quantity", 0)),
        "protein_g": round(nutrients.get("PROCNT", {}).get("quantity", 0)),
        "carbs_g": round(nutrients.get("CHOCDF", {}).get("quantity", 0)),
        "fat_g": round(nutrients.get("FAT", {}).get("quantity", 0)),
        "fiber_g": round(nutrients.get("FIBTG", {}).get("quantity", 0)),
        "sugar_g": round(nutrients.get("SUGAR", {}).get("quantity", 0)),
        "sodium_mg": round(nutrients.get("NA", {}).get("quantity", 0)),
        "serving_weight_g": round(data.get("totalWeight", 0)),
    }
