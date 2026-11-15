"""優惠券商品展示頁、安全邊界與 WEB API 回歸測試。"""
import json
from unittest.mock import patch

import pytest
from linebot.v3.messaging import FlexMessage
from modules.coupon.coupon_links import get_coupon_shop_url
from modules.coupon.coupon_postback import handle_coupon_postback
from modules.coupon.coupon_service import calculate_discount, load_coupons


@pytest.fixture
def client(monkeypatch):
    # 專題測試不向真實 LINE 平台發訊息。
    monkeypatch.setenv("CHANNEL_SECRET", "test-secret")
    monkeypatch.setenv("CHANNEL_ACCESS_TOKEN", "test-token")
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


def test_multiple_quantities_and_min_spend():
    coupons = {c["id"]: c for c in load_coupons()}
    c1 = coupons["coupon_001"]
    # 單件 320 未達門檻，第二件滿額券只折一次。
    assert calculate_discount(c1, 1)["total"] == 320
    assert calculate_discount(c1, 2)["total"] == 590
    # 高於 10 件或小於 1 件不可接受。
    for qty in (0, -1, 11, True, "1"):
        with pytest.raises(ValueError):
            calculate_discount(c1, qty)
    small = dict(c1, original_price=260)
    assert calculate_discount(small, 1)["discount"] == 0
    assert calculate_discount(small, 2)["discount"] == 50
    assert calculate_discount(coupons["coupon_002"], 2)["total"] == 648
    huge = dict(c1, discount_value=9999, min_spend=0)
    assert calculate_discount(huge)["total"] == 0


def test_shop_url_prefers_public_base_url(monkeypatch):
    monkeypatch.setenv("COUPON_PUBLIC_BASE_URL", "https://fuxing.example.org/")
    monkeypatch.setenv("VERCEL_URL", "old.vercel.app")
    assert get_coupon_shop_url("coupon_001") == "https://fuxing.example.org/coupon/shop/coupon_001"
    monkeypatch.delenv("COUPON_PUBLIC_BASE_URL")
    assert get_coupon_shop_url("coupon_002") == "https://old.vercel.app/coupon/shop/coupon_002"
    monkeypatch.setenv("VERCEL_URL", "")
    assert get_coupon_shop_url("coupon_003") is None


def test_claimed_card_has_real_shop_uri_action(monkeypatch):
    monkeypatch.setenv("COUPON_PUBLIC_BASE_URL", "https://preview.example.com")
    msg = handle_coupon_postback("coupon_claim&id=coupon_001")
    assert isinstance(msg, FlexMessage)
    card = json.loads(msg.to_json())
    data = json.dumps(card, ensure_ascii=False)
    assert '"type": "uri"' in data
    assert "https://preview.example.com/coupon/shop/coupon_001" in data
    assert "coupon_use&id=coupon_001" in data  # 保留 LINE 備援


def test_shop_page_and_quote(client):
    res = client.get("/coupon/shop/coupon_001")
    assert res.status_code == 200
    assert "復興農產禮盒" in res.get_data(as_text=True)
    assert "非實拍" in res.get_data(as_text=True)
    assert "no-store" in res.headers["Cache-Control"]
    assert client.get("/coupon/shop/not-found").status_code == 404
    ok = client.get("/api/coupon/quote/coupon_001?quantity=2")
    assert ok.status_code == 200
    assert ok.json["total"] == 590
    bad = client.get("/api/coupon/quote/coupon_001?quantity=0")
    assert bad.status_code == 400
    assert client.get("/api/coupon/quote/missing").status_code == 404


def test_complete_only_returns_demo_receipt(client):
    url = "/api/coupon/complete/coupon_002"
    ok = client.post(url, json={"quantity": 2, "total": 1, "credit_card": "ignored"})
    assert ok.status_code == 200
    assert ok.json["status"] == "demo_complete"
    assert ok.json["quote"]["total"] == 648
    assert "訂單" in ok.json["message"]
    assert client.post(url, json={"quantity": 0}).status_code == 400
    assert client.post(url, json={"quantity": "2"}).status_code == 400


def test_expired_shop_cannot_checkout(client):
    with patch("modules.coupon.coupon_web.is_expired", return_value=True):
        res = client.get("/coupon/shop/coupon_001")
        assert res.status_code == 200
        assert "優惠已到期" in res.get_data(as_text=True)
        assert client.get("/api/coupon/quote/coupon_001").status_code == 410
        assert client.post("/api/coupon/complete/coupon_001", json={"quantity": 1}).status_code == 410
