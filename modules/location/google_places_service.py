import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(
    PROJECT_ROOT / ".env"
)


from modules.location.distance import calculate_distance

PLACES_URL = (
    "https://places.googleapis.com/v1/"
    "places:searchNearby"
)


def places_enabled():
    """
    Google Places 預設關閉，
    避免開發過程意外產生 API 用量。
    """
    return (
        os.getenv(
            "PLACES_ENABLED",
            "false"
        ).lower()
        == "true"
    )


def get_places_api_key():
    return os.getenv(
        "GOOGLE_MAPS_API_KEY"
    )


def get_search_radius():
    try:
        radius = float(
            os.getenv(
                "PLACES_RADIUS_METERS",
                "10000"
            )
        )
    except ValueError:
        radius = 10000

    # Google Nearby Search 上限 50 km
    return max(
        100,
        min(radius, 50000)
    )


def search_nearby_restaurants(
    latitude,
    longitude,
    limit=5,
):
    """
    使用 Google Places Nearby Search (New)
    即時搜尋使用者附近餐廳。

    此資料不寫入本地資料庫，
    僅作為 LBS 即時 fallback。
    """

    if not places_enabled():
        return []

    api_key = get_places_api_key()

    if not api_key:
        return []

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return []

    if not (-90 <= latitude <= 90):
        return []

    if not (-180 <= longitude <= 180):
        return []

    limit = max(
        1,
        min(int(limit), 20)
    )

    radius = get_search_radius()

    payload = {
        "includedTypes": [
            "restaurant"
        ],
        "maxResultCount": limit,
        "rankPreference": "DISTANCE",
        "languageCode": "zh-TW",
        "regionCode": "TW",
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": radius,
            }
        },
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,

        # 只拿目前功能真正需要的欄位。
        # 不拿 rating / reviews / opening hours，
        # 避免升到更高價格 SKU。
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.location,"
            "places.googleMapsUri"
        ),
    }

    try:
        response = requests.post(
            PLACES_URL,
            json=payload,
            headers=headers,
            timeout=8,
        )

        response.raise_for_status()

        data = response.json()

    except (
        requests.RequestException,
        ValueError,
    ):
        return []

    results = []

    for place in data.get(
        "places",
        []
    ):
        location = place.get(
            "location",
            {}
        )

        place_latitude = location.get(
            "latitude"
        )

        place_longitude = location.get(
            "longitude"
        )

        display_name = place.get(
            "displayName",
            {}
        )

        name = display_name.get(
            "text"
        )

        if (
            not name
            or place_latitude is None
            or place_longitude is None
        ):
            continue

        distance = calculate_distance(
            latitude,
            longitude,
            place_latitude,
            place_longitude,
        )

        place_id = place.get("id", "")

        maps_url = place.get(
            "googleMapsUri"
        )

        # 如果 API 沒回 maps URI，
        # 仍可以透過 place id 建 Google Maps URL
        if not maps_url and place_id:
            maps_url = (
                "https://www.google.com/maps/"
                f"search/?api=1&query_place_id={place_id}"
            )

        item = {
            "id": (
                f"google_{place_id}"
                if place_id
                else f"google_{name}"
            ),
            "name": name,
            "category": "餐廳",
            "address": place.get(
                "formattedAddress",
                "地址資訊請查看 Google Maps",
            ),
            "latitude": float(
                place_latitude
            ),
            "longitude": float(
                place_longitude
            ),
            "distance": distance,
            "description": (
                "依照你目前的位置即時搜尋到的附近餐廳。"
            ),
            "tags": [],
            "maps_url": maps_url,
            "price_items": [],
            "source_provider": "google_maps",
            "google_place_id": place_id,
        }

        results.append(item)

    results.sort(
        key=lambda item: item["distance"]
    )

    return results[:limit]