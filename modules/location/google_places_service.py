import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from modules.location.distance import calculate_distance


logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(
    PROJECT_ROOT / ".env"
)


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
            "false",
        ).lower()
        == "true"
    )


def get_places_api_key():
    """
    取得 Google Maps API Key。

    注意：
    不要把 API Key 寫入 log。
    """
    return os.getenv(
        "GOOGLE_MAPS_API_KEY"
    )


def get_search_radius():
    """
    取得搜尋半徑。

    預設 10 km，
    並限制在 100 m ～ 50 km。
    """
    try:
        radius = float(
            os.getenv(
                "PLACES_RADIUS_METERS",
                "10000",
            )
        )

    except (TypeError, ValueError):
        logger.warning(
            "Invalid PLACES_RADIUS_METERS, "
            "fallback to 10000 meters."
        )
        radius = 10000

    return max(
        100,
        min(radius, 50000),
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

    發生 API 問題時：
    - 不讓 LINE Bot 整體崩潰
    - 回傳 []
    - 將原因記錄至 server log
    """

    # =========================
    # 功能開關
    # =========================
    if not places_enabled():
        logger.info(
            "Google Places search skipped: "
            "PLACES_ENABLED is false."
        )
        return []

    # =========================
    # API Key
    # =========================
    api_key = get_places_api_key()

    if not api_key:
        logger.warning(
            "Google Places search skipped: "
            "GOOGLE_MAPS_API_KEY is missing."
        )
        return []

    # =========================
    # 座標驗證
    # =========================
    try:
        latitude = float(latitude)
        longitude = float(longitude)

    except (TypeError, ValueError):
        logger.warning(
            "Google Places search skipped: "
            "invalid coordinate format."
        )
        return []

    if not (-90 <= latitude <= 90):
        logger.warning(
            "Google Places search skipped: "
            "latitude out of range."
        )
        return []

    if not (-180 <= longitude <= 180):
        logger.warning(
            "Google Places search skipped: "
            "longitude out of range."
        )
        return []

    # =========================
    # 回傳數量
    # =========================
    try:
        limit = int(limit)

    except (TypeError, ValueError):
        limit = 5

    limit = max(
        1,
        min(limit, 20),
    )

    radius = get_search_radius()

    # =========================
    # Google Places Request
    # =========================
    payload = {
        "includedTypes": [
            "restaurant",
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

        # 絕對不要把這個 headers
        # 整包輸出到 log
        "X-Goog-Api-Key": api_key,

        # 只取目前功能需要的欄位，
        # 避免取得不必要的 Places 資料。
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

    except requests.Timeout:
        logger.warning(
            "Google Places request timed out."
        )
        return []

    except requests.RequestException:
        logger.exception(
            "Google Places network request failed."
        )
        return []

    # =========================
    # HTTP 錯誤處理
    # =========================
    if response.status_code != 200:
        # 不輸出 headers，
        # 避免 API Key 出現在 log。
        error_text = response.text

        # 避免錯誤內容過長
        if len(error_text) > 1000:
            error_text = (
                error_text[:1000]
                + "..."
            )

        if response.status_code == 400:
            logger.warning(
                "Google Places returned HTTP 400 "
                "(invalid request). Response: %s",
                error_text,
            )

        elif response.status_code in (
            401,
            403,
        ):
            logger.error(
                "Google Places returned HTTP %s "
                "(API key / permission issue). "
                "Response: %s",
                response.status_code,
                error_text,
            )

        elif response.status_code == 429:
            logger.error(
                "Google Places returned HTTP 429 "
                "(quota / rate limit exceeded). "
                "Response: %s",
                error_text,
            )

        elif 500 <= response.status_code < 600:
            logger.error(
                "Google Places server error HTTP %s. "
                "Response: %s",
                response.status_code,
                error_text,
            )

        else:
            logger.error(
                "Google Places returned unexpected "
                "HTTP %s. Response: %s",
                response.status_code,
                error_text,
            )

        return []

    # =========================
    # JSON 解析
    # =========================
    try:
        data = response.json()

    except ValueError:
        logger.error(
            "Google Places returned invalid JSON."
        )
        return []

    places = data.get(
        "places",
        [],
    )

    if not isinstance(places, list):
        logger.error(
            "Google Places response format invalid: "
            "'places' is not a list."
        )
        return []

    if not places:
        logger.info(
            "Google Places returned no restaurants "
            "for latitude=%s longitude=%s radius=%sm.",
            latitude,
            longitude,
            radius,
        )
        return []

    # =========================
    # 資料轉換
    # =========================
    results = []

    for place in places:

        if not isinstance(place, dict):
            continue

        location = place.get(
            "location",
            {},
        )

        if not isinstance(location, dict):
            continue

        place_latitude = location.get(
            "latitude"
        )

        place_longitude = location.get(
            "longitude"
        )

        display_name = place.get(
            "displayName",
            {},
        )

        if not isinstance(
            display_name,
            dict,
        ):
            display_name = {}

        name = display_name.get(
            "text"
        )

        if (
            not name
            or place_latitude is None
            or place_longitude is None
        ):
            logger.debug(
                "Skipped incomplete Google Place result."
            )
            continue

        try:
            place_latitude = float(
                place_latitude
            )

            place_longitude = float(
                place_longitude
            )

        except (TypeError, ValueError):
            continue

        distance = calculate_distance(
            latitude,
            longitude,
            place_latitude,
            place_longitude,
        )

        place_id = place.get(
            "id",
            "",
        )

        maps_url = place.get(
            "googleMapsUri"
        )

        # 如果 Google 沒回 maps URI，
        # 使用 Place ID 建立備用 Maps URL。
        if (
            not maps_url
            and place_id
        ):
            maps_url = (
                "https://www.google.com/maps/"
                "search/?api=1"
                f"&query_place_id={place_id}"
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
            "latitude": place_latitude,
            "longitude": place_longitude,
            "distance": distance,
            "description": (
                "依照你目前的位置即時搜尋到的附近餐廳。"
            ),
            "tags": [],
            "maps_url": maps_url,
            "price_items": [],
            "source_provider": (
                "google_maps"
            ),
            "google_place_id": (
                place_id
            ),
        }

        results.append(item)

    results.sort(
        key=lambda item: item[
            "distance"
        ]
    )

    results = results[:limit]

    logger.info(
        "Google Places nearby restaurant "
        "search succeeded: %s result(s).",
        len(results),
    )

    return results