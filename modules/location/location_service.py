import json
from pathlib import Path

from modules.location.distance import calculate_distance


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "attractions.json"


def load_attractions():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def find_nearby_attractions(
    latitude,
    longitude,
    limit=3,
    category=None
):
    attractions = load_attractions()

    results = []

    for attraction in attractions:
        # 有指定分類時，只保留該分類
        if category and attraction.get("category") != category:
            continue

        distance = calculate_distance(
            latitude,
            longitude,
            attraction["latitude"],
            attraction["longitude"]
        )

        result = attraction.copy()
        result["distance"] = distance

        results.append(result)

    # 距離近的排前面
    results.sort(key=lambda place: place["distance"])

    return results[:limit]