"""優惠券 2.0 的新流程與旅遊助手按鈕測試。"""

import json
from unittest.mock import patch

from linebot.v3.messaging import FlexMessage, TextMessage

from handlers.message_handler import get_travel_assistant_message
from modules.coupon.coupon_postback import (
    create_coupon_list_message,
    handle_coupon_postback,
)
from modules.coupon.coupon_service import calculate_discount, load_coupons


def readable_json(message):
    return json.dumps(json.loads(message.to_json()), ensure_ascii=False)


def test_assistant_has_coupon_button():
    message = get_travel_assistant_message()
    assert isinstance(message, TextMessage)
    assert "優惠券" in readable_json(message)


def test_discount_totals():
    by_id = {c["id"]: c for c in load_coupons()}
    assert calculate_discount(by_id["coupon_001"])["total"] == 530
    assert calculate_discount(by_id["coupon_002"])["total"] == 324
    assert calculate_discount(by_id["coupon_003"])["total"] == 400


def test_coupon_full_funnel():
    list_message = create_coupon_list_message()
    assert isinstance(list_message, FlexMessage)
    assert "coupon_detail" in readable_json(list_message)
    assert "查看優惠" in readable_json(list_message)

    detail = handle_coupon_postback("coupon_detail&id=coupon_001")
    assert isinstance(detail, FlexMessage)
    assert "立即領取" in readable_json(detail)

    claimed = handle_coupon_postback("coupon_claim&id=coupon_001")
    assert isinstance(claimed, FlexMessage)
    assert "立即使用" in readable_json(claimed)

    checkout = handle_coupon_postback("coupon_use&id=coupon_001")
    assert isinstance(checkout, FlexMessage)
    assert "NT$530" in readable_json(checkout)
    assert "coupon_confirm" in readable_json(checkout)

    done = handle_coupon_postback("coupon_confirm&id=coupon_001")
    assert isinstance(done, TextMessage)
    assert "折扣試算完成" in done.text
    assert "不會產生實際訂單或付款" in done.text


def test_expired_coupon_cannot_be_claimed_or_checkout():
    with patch("modules.coupon.coupon_postback.is_expired", return_value=True):
        for action in ("coupon_claim", "coupon_use", "coupon_confirm"):
            message = handle_coupon_postback(f"{action}&id=coupon_001")
            assert isinstance(message, TextMessage)
            assert "過展示期限" in message.text
