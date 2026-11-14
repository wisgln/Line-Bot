import json
from datetime import date
from types import SimpleNamespace as S
from unittest.mock import patch

from linebot.v3.messaging import FlexMessage, TextMessage

from handlers import message_handler
from modules.coupon.coupon_postback import (
    create_coupon_list_message,
    handle_coupon_postback,
)
from modules.coupon.coupon_service import (
    get_coupon,
    is_expired,
    load_coupons,
)


def readable_json(message):
    return json.dumps(
        json.loads(message.to_json()),
        ensure_ascii=False,
    )


def test_all_coupons_are_demo_only():
    coupons = load_coupons()

    assert len(coupons) == 3
    assert all(item["demo_only"] is True for item in coupons)
    assert all(
        "不可於任何實體店家折抵" in item["conditions"]
        for item in coupons
    )


def test_coupon_lookup_and_expiration():
    coupon = get_coupon("coupon_001")

    assert coupon is not None
    assert coupon["title"] == "復興農產好禮"
    assert is_expired(
        coupon,
        today=date(2026, 11, 3),
    ) is False
    assert is_expired(
        coupon,
        today=date(2027, 1, 1),
    ) is True
    assert get_coupon("missing") is None


def test_coupon_list_is_flex_and_has_demo_notice():
    message = create_coupon_list_message()

    assert isinstance(message, FlexMessage)

    payload = readable_json(message)

    assert "優惠券專區" in payload
    assert "非實際商家活動" in payload
    assert "coupon_detail" in payload


def test_coupon_claim_and_use_flow():
    claimed = handle_coupon_postback(
        "coupon_claim&id=coupon_001"
    )

    assert isinstance(claimed, FlexMessage)

    claimed_payload = readable_json(claimed)

    assert "已加入優惠券" in claimed_payload
    assert "coupon_use" in claimed_payload

    confirm = handle_coupon_postback(
        "coupon_use&id=coupon_001"
    )

    assert isinstance(confirm, FlexMessage)

    confirm_payload = readable_json(confirm)

    assert "確認試算" in confirm_payload
    assert "coupon_confirm" in confirm_payload

    done = handle_coupon_postback(
        "coupon_confirm&id=coupon_001"
    )

    assert isinstance(done, TextMessage)
    assert "折扣試算完成" in done.text
    assert "未向任何實體商家" in done.text


def test_invalid_coupon_returns_friendly_message():
    message = handle_coupon_postback(
        "coupon_claim&id=missing"
    )

    assert isinstance(message, TextMessage)
    assert "資料已更新" in message.text


def test_coupon_text_entry_does_not_use_ai():
    with patch.object(message_handler, "ApiClient"), \
            patch.object(
                message_handler,
                "MessagingApi",
            ) as api, \
            patch.object(
                message_handler,
                "get_ai_reply",
            ) as ai:

        event = S(
            message=S(text="優惠券"),
            source=S(user_id="offline"),
            reply_token="offline",
        )

        message_handler.handle_text_message(
            event,
            None,
        )

        message = (
            api.return_value
            .reply_message
            .call_args
            .args[0]
            .messages[0]
        )

        assert isinstance(message, FlexMessage)
        ai.assert_not_called()
