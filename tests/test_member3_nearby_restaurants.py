from linebot.v3.messaging import FlexMessage, TextMessage

from modules.location import merchant_location_service
from modules.location.restaurant_postback import (
    handle_nearby_restaurants,
)


def test_nearby_restaurant_no_location_data(monkeypatch):
    """
    沒有餐廳座標時，應正常回傳建置中訊息。
    """

    monkeypatch.setattr(
        merchant_location_service,
        "load_merchant_locations",
        lambda: {},
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
    有商家座標時，應產生附近餐廳 Flex Message。
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

    message = handle_nearby_restaurants(
        "nearby_restaurants&lat=24.81&lng=121.35"
    )

    assert isinstance(message, FlexMessage)


def test_nearby_restaurant_distance_order(monkeypatch):
    """
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
    )

    assert len(results) == 3

    assert (
        results[0]["distance"]
        <= results[1]["distance"]
        <= results[2]["distance"]
    )