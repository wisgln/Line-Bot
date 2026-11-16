import json
from pathlib import Path

from modules.location.distance import (
    calculate_distance,
)
from modules.merchant.merchant_service import (
    load_merchants,
)
from modules.location.google_places_service import (
    search_nearby_restaurants,
)


PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)

LOCATION_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "merchant_locations.json"
)


def load_merchant_locations():
    """
    讀取我們自己維護的商家座標資料。
    """

    if not LOCATION_DATA_PATH.exists():
        return {}

    with LOCATION_DATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "merchant_locations.json "
            "必須為 JSON object"
        )

    return data


def find_local_nearby_merchants(
    latitude,
    longitude,
    category="餐廳",
    max_distance_km=10.0,
):
    """
    從自己的商家資料庫尋找附近店家。
    """

    merchants = load_merchants()
    locations = load_merchant_locations()

    results = []

    for merchant in merchants:

        if (
            category
            and merchant.get("category")
            != category
        ):
            continue

        merchant_id = merchant.get("id")

        location = locations.get(
            merchant_id
        )

        if not location:
            continue

        merchant_latitude = (
            location.get("latitude")
        )

        merchant_longitude = (
            location.get("longitude")
        )

        if (
            merchant_latitude is None
            or merchant_longitude is None
        ):
            continue

        distance = calculate_distance(
            latitude,
            longitude,
            merchant_latitude,
            merchant_longitude,
        )

        # 太遠的本地資料不要硬塞給使用者
        if (
            max_distance_km is not None
            and distance > max_distance_km
        ):
            continue

        item = merchant.copy()

        item["latitude"] = (
            merchant_latitude
        )

        item["longitude"] = (
            merchant_longitude
        )

        item["distance"] = distance

        item["source_provider"] = (
            "local"
        )

        results.append(item)

    results.sort(
        key=lambda item: item["distance"]
    )

    return results


def merchant_identity(merchant):
    """
    用簡單店名正規化進行去重。
    """

    name = str(
        merchant.get("name", "")
    )

    return (
        name
        .replace(" ", "")
        .replace("　", "")
        .lower()
    )


def merge_merchants(
    local_results,
    external_results,
):
    """
    本地資料優先。
    Google Places 只補不足的資料。
    """

    merged = []
    seen = set()

    for merchant in (
        local_results
        + external_results
    ):
        identity = merchant_identity(
            merchant
        )

        if not identity:
            continue

        if identity in seen:
            continue

        seen.add(identity)
        merged.append(merchant)

    merged.sort(
        key=lambda item: item.get(
            "distance",
            float("inf"),
        )
    )

    return merged


def find_nearby_merchants(
    latitude,
    longitude,
    limit=5,
    category="餐廳",
    max_distance_km=10.0,
    allow_external=True,
):
    """
    混合式附近商家推薦。

    1. 優先使用自己的商家資料
    2. 不足時才使用 Google Places
    3. 合併後依距離排序
    """

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return []

    limit = max(
        1,
        min(int(limit), 20)
    )

    local_results = (
        find_local_nearby_merchants(
            latitude,
            longitude,
            category=category,
            max_distance_km=max_distance_km,
        )
    )

    # 本地資料已經夠，就完全不打 API
    if len(local_results) >= limit:
        return local_results[:limit]

    # 非餐廳暫時不使用 Places fallback
    if (
        not allow_external
        or category != "餐廳"
    ):
        return local_results[:limit]

    missing_count = (
        limit - len(local_results)
    )

    external_results = (
        search_nearby_restaurants(
            latitude,
            longitude,
            limit=max(
                missing_count * 2,
                5,
            ),
        )
    )

    results = merge_merchants(
        local_results,
        external_results,
    )

    return results[:limit]