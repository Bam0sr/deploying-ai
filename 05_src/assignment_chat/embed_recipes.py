"""One-time script to build local recipe embeddings."""

import json
import os
import string
import time

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")
RECIPES_JSON = os.path.join(DATA_DIR, "recipes.json")

MEALDB_SEARCH_URL = "https://www.themealdb.com/api/json/v1/1/search.php"


def fetch_all_recipes() -> list[dict]:
    """Fetch recipes from TheMealDB, letter by letter."""
    all_meals = {}
    for letter in string.ascii_lowercase:
        print(f"fetching meals starting with '{letter}'...")
        try:
            resp = requests.get(MEALDB_SEARCH_URL, params={"f": letter}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  error fetching '{letter}': {e}")
            continue

        meals = data.get("meals")
        if not meals:
            continue

        for meal in meals:
            meal_id = meal.get("idMeal")
            if meal_id and meal_id not in all_meals:
                all_meals[meal_id] = meal

        time.sleep(0.3) # To avoid rate limiting cause i remember from my past projects that this is a thing

    return list(all_meals.values())


def parse_ingredients(meal: dict) -> list[str]:
    """Pull non-empty ingredient + measure pairs."""
    ingredients = []
    for i in range(1, 21):
        ingredient = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if ingredient:
            ingredients.append(f"{measure} {ingredient}".strip())
    return ingredients


def meal_to_document(meal: dict) -> str:
    """Convert a meal dict into one text document."""
    name = meal.get("strMeal", "Unknown")
    category = meal.get("strCategory", "Unknown")
    area = meal.get("strArea", "Unknown")
    instructions = meal.get("strInstructions", "")
    ingredients = parse_ingredients(meal)

    return (
        f"Recipe: {name}\n"
        f"Category: {category}\n"
        f"Cuisine: {area}\n"
        f"Ingredients: {', '.join(ingredients)}\n"
        f"Instructions: {instructions}"
    )


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("=== Fetching recipes from TheMealDB ===")
    meals = fetch_all_recipes()
    print(f"Fetched {len(meals)} unique recipes.\n")

    with open(RECIPES_JSON, "w", encoding="utf-8") as f:
        json.dump(meals, f, indent=2, ensure_ascii=False)
    print(f"Saved raw recipes to {RECIPES_JSON}")

    documents = []
    ids = []
    metadatas = []
    for meal in meals:
        doc = meal_to_document(meal)
        meal_id = meal["idMeal"]
        documents.append(doc)
        ids.append(f"recipe_{meal_id}")
        metadatas.append({
            "name": meal.get("strMeal", ""),
            "category": meal.get("strCategory", ""),
            "area": meal.get("strArea", ""),
        })

    print(f"\n======= Embedding {len(documents)} recipes into ChromaDB ===")
    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2",
    )

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection("recipes")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name="recipes",
        embedding_function=embedding_fn,
    )

    batch_size = 50
    for i in range(0, len(documents), batch_size):
        end = min(i + batch_size, len(documents))
        print(f"  adding batch {i}–{end - 1}...")
        collection.add(
            documents=documents[i:end],
            ids=ids[i:end],
            metadatas=metadatas[i:end],
        )

    print(f"\nDone! ChromaDB persisted to {CHROMA_DIR}")
    print(f"Collection '{collection.name}' has {collection.count()} documents.")


if __name__ == "__main__":
    main()
