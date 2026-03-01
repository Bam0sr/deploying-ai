"""Service 1: TheMealDB API."""

import requests
from langchain.tools import tool
from utils.logger import get_logger

_logs = get_logger(__name__)

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"


def _parse_meal(meal: dict) -> str:
    """Convert one MealDB entry to plain text."""
    name = meal.get("strMeal", "Unknown")
    category = meal.get("strCategory", "")
    area = meal.get("strArea", "")
    instructions = meal.get("strInstructions", "")

    ingredients = []
    for i in range(1, 21):
        ing = (meal.get(f"strIngredient{i}") or "").strip()
        msr = (meal.get(f"strMeasure{i}") or "").strip()
        if ing:
            ingredients.append(f"{msr} {ing}".strip())

    return (
        f"Name: {name}\n"
        f"Category: {category}\n"
        f"Cuisine: {area}\n"
        f"Ingredients: {', '.join(ingredients)}\n"
        f"Instructions: {instructions[:500]}"
    )


@tool
def search_meal(query: str) -> str:
    """Find meals by name and return recipe details."""
    _logs.info(f"[API] Searching TheMealDB for: '{query}'")
    try:
        resp = requests.get(
            f"{MEALDB_BASE}/search.php", params={"s": query}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error contacting TheMealDB: {e}"

    meals = data.get("meals")
    if not meals:
        _logs.info(f"[API] No meals found for '{query}'")
        return f"No meals found for '{query}'."

    _logs.info(f"[API] Found {len(meals)} meal(s): {[m.get('strMeal') for m in meals[:3]]}")
    results = [_parse_meal(m) for m in meals[:3]]
    return "\n---\n".join(results)


@tool
def random_meal() -> str:
    """Get one random meal from TheMealDB."""
    try:
        resp = requests.get(f"{MEALDB_BASE}/random.php", timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error contacting TheMealDB: {e}"

    meals = data.get("meals")
    if not meals:
        return "Could not fetch a random meal."

    return _parse_meal(meals[0])
