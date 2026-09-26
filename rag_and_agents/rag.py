"""
Nutrition Knowledge Agent's retrieval layer.

Two data sources, tried in order:
1. A small local text search built from data/foods.json (fast, works offline,
   good for the demo's common foods).
2. USDA FoodData Central's free public API (real, huge database) for anything
   the local set doesn't cover.

This is the "Food Data RAG Retrieval" piece from the problem statement.
"""
import json
import os
from pathlib import Path
import requests

DATA_PATH = Path(__file__).parent.parent / "data" / "foods.json"

_foods = None

def _build_index():
    """Load the local database into memory."""
    global _foods
    with open(DATA_PATH) as f:
        _foods = json.load(f)

def search_local(query, k=3):
    """Semantic search replaced with a direct keyword search to remove OpenAI dependency."""
    global _foods
    if _foods is None:
        _build_index()

    query_lower = query.lower()
    results = []
    for food in _foods:
        if query_lower in food.get("name", "").lower() or query_lower in food.get("notes", "").lower():
            results.append(food)
            
    return results[:k]

def search_usda(query, page_size=3):
    """Fall back to the live USDA FoodData Central API for foods not in the
    local seed set. Free, no key needed for light use (DEMO_KEY works)."""
    api_key = os.environ.get("USDA_API_KEY", "DEMO_KEY")
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"query": query, "pageSize": page_size, "api_key": api_key}

    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return [{"name": query, "error": f"USDA lookup failed: {e}"}]

    results = []
    for food in data.get("foods", []):
        nutrients = {n["nutrientName"]: n["value"] for n in food.get("foodNutrients", [])}
        results.append({
            "name": food.get("description", query),
            "calories": nutrients.get("Energy"),
            "protein_g": nutrients.get("Protein"),
            "carbs_g": nutrients.get("Carbohydrate, by difference"),
            "fat_g": nutrients.get("Total lipid (fat)"),
            "notes": "Source: USDA FoodData Central",
        })
    return results

def get_nutrition_info(food_query):
    """Public entry point the agents call. Tries local search first, then USDA."""
    local_hits = search_local(food_query)
    if local_hits:
        return local_hits
    return search_usda(food_query)
    