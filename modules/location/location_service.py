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

    category 可以是 None（全部）、一個字串，或一組類別（tuple / list）。

    smart_rank=True：依距離 + 營業狀態排序
    smart_rank=False：單純依照距離排序
    """

    attractions = load_attractions()

    if isinstance(category, str):
        categories = (category,)
    elif category:
        categories = tuple(category)
    else:
        categories = None

    results = []

    for attraction in attractions:
        # 指定分類時只保留符合的類別
        if categories and attraction.get("category") not in categories:
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
        # 篩選後的結果都已經屬於選定的類別，不需要再給分類加分，
        # 一組類別時不傳 preferred_category，避免他的排序收到不認得的格式。
        preferred = category if isinstance(category, str) else None
        results = rank_attractions(
            results,
            preferred_category=preferred
        )
    else:
        results.sort(key=lambda place: place["distance"])

    # 排完之後才取前 N 名
    return results[:limit]