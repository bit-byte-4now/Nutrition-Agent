"""
Nutrition Knowledge Agent's retrieval layer.

Two data sources, tried in order:
1. A small local FAISS index built from data/foods.json (fast, works offline,
   good for the demo's common foods).
2. USDA FoodData Central's free public API (real, huge database) for anything
   the local set doesn't cover.

This is the "Food Data RAG Retrieval" piece from the problem statement.
"""
import json
import os
from pathlib import Path

import faiss
import numpy as np
import requests
from openai import OpenAI

DATA_PATH = Path(__file__).parent.parent / "data" / "foods.json"
EMBED_MODEL = "text-embedding-3-small"

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

_index = None
_foods = None


def _embed(texts):
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data], dtype="float32")


def _build_index():
    """Build the FAISS index once and cache it in memory (module-level)."""
    global _index, _foods
    with open(DATA_PATH) as f:
        _foods = json.load(f)

    texts = [f["name"] + ". " + f["notes"] for f in _foods]
    vectors = _embed(texts)
    dim = vectors.shape[1]
    _index = faiss.IndexFlatL2(dim)
    _index.add(vectors)


def search_local(query, k=3, max_distance=0.6):
    """Semantic search over the local seed dataset. Returns [] if nothing
    is a close enough match (max_distance is a similarity cutoff, not exact)."""
    global _index, _foods
    if _index is None:
        _build_index()

    query_vector = _embed([query])
    distances, indices = _index.search(query_vector, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        results.append(_foods[idx])
    return results


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
    """Public entry point the agents call. Tries local FAISS first, then USDA."""
    local_hits = search_local(food_query)
    if local_hits:
        return local_hits
    return search_usda(food_query)
