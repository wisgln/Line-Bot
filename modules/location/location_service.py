import json
from pathlib import Path

from modules.location.distance import calculate_distance
from modules.location.recommendation import rank_attractions


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "attractions.json"


def load_attractions():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def find_nearby_attractions(
    latitude,
    longitude,
    limit=5,
    category=None,
    smart_rank=False
):
    """
    尋找附近景點。

    smart_rank=True：
        依距離 + 營業狀態 + 分類偏好進行智慧排序

    smart_rank=False：
        單純依照距離排序
    """

    attractions = load_attractions()
    results = []

    for attraction in attractions:

        # 指定分類時只保留符合項目
        if category and attraction.get("category") != category:
            continue

        # 沒有有效座標就跳過
        if (
            attraction.get("latitude") is None
            or attraction.get("longitude") is None
        ):
            continue

        distance = calculate_distance(
            latitude,
            longitude,
            attraction["latitude"],
            attraction["longitude"]
        )

        item = attraction.copy()
        item["distance"] = distance

        results.append(item)

    if smart_rank:
        results = rank_attractions(
            results,
            preferred_category=category
        )

    else:
        results.sort(
            key=lambda place: place["distance"]
        )

    # 排完之後才取前 N 名
    return results[:limit]