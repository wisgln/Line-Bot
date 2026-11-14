"""優惠券 3.1：滿額門檻與在地體驗人數呈現。"""
import pytest
from modules.coupon.coupon_service import calculate_discount, load_coupons


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CHANNEL_SECRET", "unit-test-secret")
    monkeypatch.setenv("CHANNEL_ACCESS_TOKEN", "unit-test-token")
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


def test_threshold_price_changes_with_quantity():
    coupons = {coupon["id"]: coupon for coupon in load_coupons()}
    c = coupons["coupon_001"]
    assert calculate_discount(c, 1) == {"quantity": 1, "original": 320, "discount": 0, "total": 320}
    assert calculate_discount(c, 2) == {"quantity": 2, "original": 640, "discount": 50, "total": 590}
    assert calculate_discount(c, 3)["total"] == 910


def test_web_page_displays_threshold_hint(client):
    html = client.get("/coupon/shop/coupon_001").get_data(as_text=True)
    assert 'data-unit-price="320"' in html
    assert 'data-min-spend="500"' in html
    assert 'id="threshold-hint"' in html
    assert "優惠試算" in html
    assert "優惠已套用" not in html
    assert "YOUR COUPON" not in html


def test_experience_page_uses_people_not_items(client):
    html = client.get("/coupon/shop/coupon_003").get_data(as_text=True)
    assert "體驗人數" in html
    assert "每人費用" in html
    assert 'data-quantity-unit="位"' in html
    js = client.get("/static/js/coupon-shop.js").get_data(as_text=True)
    assert "quantityUnit" in js
    assert "thresholdHint" in js


def test_quote_api_calculates_on_server(client):
    first = client.get("/api/coupon/quote/coupon_001?quantity=1")
    second = client.get("/api/coupon/quote/coupon_001?quantity=2")
    assert first.json["discount"] == 0
    assert second.json["discount"] == 50
    assert second.json["total"] == 590
