from modules.location import location_service
from modules.location.category_menu import (
    create_category_quick_reply,
)


def fake_attractions():
    return [
        {
            "id": 1,
            "name": "測試自然景點",
            "category": "自然景觀",
            "latitude": 24.81,
            "longitude": 121.35,
            "opening_hours": "24小時",
            "address": "測試地址 1",
        },
        {
            "id": 2,
            "name": "測試文化景點",
            "category": "歷史文化",
            "latitude": 24.82,
            "longitude": 121.36,
            "opening_hours": "09:00-17:00",
            "address": "測試地址 2",
        },
        {
            "id": 3,
            "name": "測試部落景點",
            "category": "部落文化",
            "latitude": 24.85,
            "longitude": 121.38,
            "opening_hours": "全天開放",
            "address": "測試地址 3",
        },
    ]


def test_nearby_attractions_distance_order(monkeypatch):
    """
    純距離模式應由近到遠排序。
    """

    monkeypatch.setattr(
        location_service,
        "load_attractions",
        fake_attractions,
    )

    results = location_service.find_nearby_attractions(
        24.81,
        121.35,
        limit=3,
        smart_rank=False,
    )

    assert len(results) == 3

    assert (
        results[0]["distance"]
        <= results[1]["distance"]
        <= results[2]["distance"]
    )


def test_nearby_attractions_category_filter(monkeypatch):
    """
    指定分類時，只能回傳符合分類的景點。
    """

    monkeypatch.setattr(
        location_service,
        "load_attractions",
        fake_attractions,
    )

    results = location_service.find_nearby_attractions(
        24.81,
        121.35,
        limit=5,
        category="自然景觀",
        smart_rank=False,
    )

    assert len(results) == 1
    assert results[0]["category"] == "自然景觀"
    assert results[0]["name"] == "測試自然景點"


def test_smart_ranking_generates_score(monkeypatch):
    """
    開啟智慧排序後，每個景點應產生推薦分數。
    """

    monkeypatch.setattr(
        location_service,
        "load_attractions",
        fake_attractions,
    )

    results = location_service.find_nearby_attractions(
        24.81,
        121.35,
        limit=3,
        smart_rank=True,
    )

    assert len(results) == 3

    for attraction in results:
        assert "recommendation_score" in attraction
        assert isinstance(
            attraction["recommendation_score"],
            (int, float),
        )

    # 推薦分數應由高到低
    scores = [
        attraction["recommendation_score"]
        for attraction in results
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_location_quick_reply():
    """
    LBS Quick Reply 應包含景點分類與附近餐廳。
    """

    quick_reply = create_category_quick_reply(
        24.81,
        121.35,
    )

    json_text = quick_reply.to_json()

    assert "location_filter" in json_text
    assert "nearby_restaurants" in json_text
    assert "24.81" in json_text
    assert "121.35" in json_text