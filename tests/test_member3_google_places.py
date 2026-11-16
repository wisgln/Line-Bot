import logging

import requests

from modules.location import google_places_service


def test_places_disabled_does_not_call_api(
    monkeypatch,
):
    """
    PLACES_ENABLED=false 時，
    不應呼叫 Google API。
    """

    monkeypatch.setenv(
        "PLACES_ENABLED",
        "false",
    )

    monkeypatch.setenv(
        "GOOGLE_MAPS_API_KEY",
        "test-key",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "Google API should not be called"
        )

    monkeypatch.setattr(
        google_places_service.requests,
        "post",
        fail_if_called,
    )

    results = (
        google_places_service
        .search_nearby_restaurants(
            24.81,
            121.35,
            5,
        )
    )

    assert results == []


def test_missing_api_key_does_not_call_api(
    monkeypatch,
):
    """
    啟用 Places 但沒有 API Key 時，
    應安全回傳空列表。
    """

    monkeypatch.setenv(
        "PLACES_ENABLED",
        "true",
    )

    monkeypatch.delenv(
        "GOOGLE_MAPS_API_KEY",
        raising=False,
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "Google API should not be called"
        )

    monkeypatch.setattr(
        google_places_service.requests,
        "post",
        fail_if_called,
    )

    results = (
        google_places_service
        .search_nearby_restaurants(
            24.81,
            121.35,
            5,
        )
    )

    assert results == []


def test_invalid_coordinate_does_not_call_api(
    monkeypatch,
):
    """
    非法座標不應送到 Google API。
    """

    monkeypatch.setenv(
        "PLACES_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "GOOGLE_MAPS_API_KEY",
        "test-key",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "Google API should not be called"
        )

    monkeypatch.setattr(
        google_places_service.requests,
        "post",
        fail_if_called,
    )

    results = (
        google_places_service
        .search_nearby_restaurants(
            "abc",
            121.35,
            5,
        )
    )

    assert results == []


def test_google_places_http_403(
    monkeypatch,
    caplog,
):
    """
    Google API 回 403 時，
    不應造成 LINE Bot 崩潰。
    """

    monkeypatch.setenv(
        "PLACES_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "GOOGLE_MAPS_API_KEY",
        "test-key",
    )

    class FakeResponse:
        status_code = 403
        text = (
            '{"error":"permission denied"}'
        )

    monkeypatch.setattr(
        google_places_service.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(),
    )

    with caplog.at_level(
        logging.ERROR
    ):
        results = (
            google_places_service
            .search_nearby_restaurants(
                24.81,
                121.35,
                5,
            )
        )

    assert results == []
    assert "403" in caplog.text


def test_google_places_timeout(
    monkeypatch,
    caplog,
):
    """
    Google API timeout 時，
    應安全回傳空列表。
    """

    monkeypatch.setenv(
        "PLACES_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "GOOGLE_MAPS_API_KEY",
        "test-key",
    )

    def raise_timeout(*args, **kwargs):
        raise requests.Timeout()

    monkeypatch.setattr(
        google_places_service.requests,
        "post",
        raise_timeout,
    )

    with caplog.at_level(
        logging.WARNING
    ):
        results = (
            google_places_service
            .search_nearby_restaurants(
                24.81,
                121.35,
                5,
            )
        )

    assert results == []
    assert "timed out" in caplog.text


def test_google_places_success(
    monkeypatch,
):
    """
    Google Places 正常回傳時，
    應轉換為系統使用的餐廳格式。
    """

    monkeypatch.setenv(
        "PLACES_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "GOOGLE_MAPS_API_KEY",
        "test-key",
    )

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {
                "places": [
                    {
                        "id": "place_001",
                        "displayName": {
                            "text": "測試餐廳"
                        },
                        "formattedAddress":
                            "桃園市測試路1號",
                        "location": {
                            "latitude": 24.811,
                            "longitude": 121.351,
                        },
                        "googleMapsUri":
                            "https://maps.google.com/"
                            "?q=test",
                    }
                ]
            }

    monkeypatch.setattr(
        google_places_service.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(),
    )

    results = (
        google_places_service
        .search_nearby_restaurants(
            24.81,
            121.35,
            5,
        )
    )

    assert len(results) == 1

    restaurant = results[0]

    assert restaurant["name"] == "測試餐廳"
    assert restaurant["category"] == "餐廳"
    assert (
        restaurant["source_provider"]
        == "google_maps"
    )
    assert (
        restaurant["google_place_id"]
        == "place_001"
    )
    assert restaurant["distance"] >= 0