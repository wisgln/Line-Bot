from linebot.v3.messaging import FlexMessage, TextMessage

from modules.location import merchant_location_service
from modules.location.restaurant_postback import (
    handle_nearby_restaurants,
)


def test_nearby_restaurant_no_location_data(monkeypatch):
    """
    本地與外部都沒有餐廳資料時，
    應正常回傳建置中訊息。
    """

    monkeypatch.setattr(
        merchant_location_service,
        "load_merchant_locations",
        lambda: {},
    )

    # 測試時禁止真的呼叫 Google Places
    monkeypatch.setattr(
        merchant_location_service,
        "search_nearby_restaurants",
        lambda latitude, longitude, limit=5: [],
    )

    message = handle_nearby_restaurants(
        "nearby_restaurants&lat=24.81&lng=121.35"
    )

    assert isinstance(message, TextMessage)
    assert "建置中" in message.text


def test_nearby_restaurant_invalid_location():
    """
    座標格式錯誤時，不應造成系統崩潰。
    """

    message = handle_nearby_restaurants(
        "nearby_restaurants&lat=abc&lng=xyz"
    )

    assert isinstance(message, TextMessage)
    assert "位置資料有誤" in message.text


def test_nearby_restaurant_flex_message(monkeypatch):
    """
    有本地商家座標時，
    應產生附近餐廳 Flex Message。
    """

    fake_locations = {
        "merchant_001": {
            "latitude": 24.82,
            "longitude": 121.35,
        },
        "merchant_002": {
            "latitude": 24.81,
            "longitude": 121.36,
        },
        "merchant_003": {
            "latitude": 24.80,
            "longitude": 121.37,
        },
    }

    monkeypatch.setattr(
        merchant_location_service,
        "load_merchant_locations",
        lambda: fake_locations,
    )

    # 測試時不要為了補足 5 家而真的打 Google Places
    monkeypatch.setattr(
        merchant_location_service,
        "search_nearby_restaurants",
        lambda latitude, longitude, limit=5: [],
    )

    message = handle_nearby_restaurants(
        "nearby_restaurants&lat=24.81&lng=121.35"
    )

    assert isinstance(message, FlexMessage)


def test_nearby_restaurant_distance_order(monkeypatch):
    """
    不限制搜尋距離時，
    附近餐廳應依距離由近到遠排序。
    """

    fake_locations = {
        "merchant_001": {
            "latitude": 24.90,
            "longitude": 121.35,
        },
        "merchant_002": {
            "latitude": 24.8101,
            "longitude": 121.3501,
        },
        "merchant_003": {
            "latitude": 24.85,
            "longitude": 121.35,
        },
    }

    monkeypatch.setattr(
        merchant_location_service,
        "load_merchant_locations",
        lambda: fake_locations,
    )

    results = merchant_location_service.find_nearby_merchants(
        24.81,
        121.35,
        limit=3,
        category="餐廳",
        max_distance_km=None,
        allow_external=False,
    )

    assert len(results) == 3

    assert (
        results[0]["distance"]
        <= results[1]["distance"]
        <= results[2]["distance"]
    )


def test_nearby_restaurant_radius_filter(monkeypatch):
    """
    10 km 內餐廳保留，
    超過 10 km 的餐廳排除。
    """

    fake_locations = {
        "merchant_001": {
            "latitude": 24.8101,
            "longitude": 121.3501,
        },
        "merchant_002": {
            "latitude": 24.95,
            "longitude": 121.35,
        },
        "merchant_003": {
            "latitude": 25.10,
            "longitude": 121.35,
        },
    }

    monkeypatch.setattr(
        merchant_location_service,
        "load_merchant_locations",
        lambda: fake_locations,
    )

    results = merchant_location_service.find_nearby_merchants(
        24.81,
        121.35,
        limit=5,
        category="餐廳",
        max_distance_km=10,
        allow_external=False,
    )

    assert len(results) == 1
    assert results[0]["id"] == "merchant_001"
    assert results[0]["distance"] <= 10


def test_google_places_fallback(monkeypatch):
    """
    本地餐廳不足時，
    應可使用外部 Places 結果補足。
    """

    monkeypatch.setattr(
        merchant_location_service,
        "load_merchant_locations",
        lambda: {},
    )

    fake_external = [
        {
            "id": "google_test_001",
            "name": "測試附近餐廳",
            "category": "餐廳",
            "address": "測試地址",
            "latitude": 24.811,
            "longitude": 121.351,
            "distance": 0.15,
            "description": "測試資料",
            "tags": [],
            "maps_url": "https://www.google.com/maps/",
            "price_items": [],
            "source_provider": "google_maps",
        }
    ]

    monkeypatch.setattr(
        merchant_location_service,
        "search_nearby_restaurants",
        lambda latitude, longitude, limit=5: fake_external,
    )

    results = merchant_location_service.find_nearby_merchants(
        24.81,
        121.35,
        limit=5,
        category="餐廳",
        allow_external=True,
    )

    assert len(results) == 1
    assert results[0]["name"] == "測試附近餐廳"
    assert results[0]["source_provider"] == "google_maps"