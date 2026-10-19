import json
from pathlib import Path

from modules.location.distance import calculate_distance
from modules.merchant.merchant_service import load_merchants


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCATION_DATA_PATH = PROJECT_ROOT / "data" / "merchant_locations.json"


def load_merchant_locations():
    """
    讀取商家經緯度資料。

    格式：
    {
        "merchant_001": {
            "latitude": 24.123,
            "longitude": 121.456
        }
    }
    """

    if not LOCATION_DATA_PATH.exists():
        return {}

    with LOCATION_DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("merchant_locations.json 必須為 JSON object")

    return data


def find_nearby_merchants(
    latitude,
    longitude,
    limit=5,
    category="餐廳"
):
    """
    根據使用者位置尋找附近商家。

    預設只找餐廳。
    """

    merchants = load_merchants()
    locations = load_merchant_locations()

    results = []

    for merchant in merchants:
        # 只找指定類型
        if category and merchant.get("category") != category:
            continue

        merchant_id = merchant.get("id")
        location = locations.get(merchant_id)

        # 沒有座標資料先跳過
        if not location:
            continue

        merchant_latitude = location.get("latitude")
        merchant_longitude = location.get("longitude")

        if merchant_latitude is None or merchant_longitude is None:
            continue

        distance = calculate_distance(
            latitude,
            longitude,
            merchant_latitude,
            merchant_longitude
        )

        item = merchant.copy()
        item["latitude"] = merchant_latitude
        item["longitude"] = merchant_longitude
        item["distance"] = distance

        results.append(item)

    results.sort(
        key=lambda item: item["distance"]
    )

    return results[:limit]