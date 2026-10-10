import json
from pathlib import Path

from modules.location.distance import calculate_distance


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "attractions.json"


def load_attractions():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def find_nearby_attractions(latitude, longitude, limit=3):
    attractions = load_attractions()

    results = []

    for attraction in attractions:
        distance = calculate_distance(
            latitude,
            longitude,
            attraction["latitude"],
            attraction["longitude"]
        )

        result = attraction.copy()
        result["distance"] = distance

        results.append(result)

    results.sort(key=lambda place: place["distance"])

    return results[:limit]