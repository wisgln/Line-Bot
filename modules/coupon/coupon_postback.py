"""優惠券 LINE 訊息與 Postback 流程。"""

import logging
from urllib.parse import parse_qs

from linebot.v3.messaging import (
    FlexContainer,
    FlexMessage,
    TextMessage,
)

from modules.coupon.coupon_flex import (
    create_coupon_bubble,
    create_coupon_carousel,
)
from modules.coupon.coupon_service import (
    get_coupon,
    load_coupons,
)

logger = logging.getLogger(__name__)


def _coupon_id(data):
    if "&" not in data:
        return None

    try:
        params = parse_qs(data.split("&", 1)[1])
        return params["id"][0]
    except (KeyError, IndexError):
        return None


def _flex(alt_text, contents):
    return FlexMessage(
        alt_text=alt_text[:100],
        contents=FlexContainer.from_dict(contents),
    )


def create_coupon_list_message():
    try:
        coupons = load_coupons()
        carousel = create_coupon_carousel(coupons)
    except (OSError, ValueError):
        logger.exception("Coupon data unavailable")
        return TextMessage(
            text="🎟️ 優惠券資料暫時無法讀取，請稍後再試。"
        )

    if not carousel:
        return TextMessage(
            text="🎟️ 目前沒有可展示的優惠券。"
        )

    return _flex(
        "復興區專題示範優惠券",
        carousel,
    )


def _get_coupon_or_error(data):
    coupon_id = _coupon_id(data)

    if not coupon_id:
        return None, TextMessage(
            text="優惠券資料有誤，請重新開啟優惠券專區。"
        )

    try:
        coupon = get_coupon(coupon_id)
    except (OSError, ValueError):
        logger.exception("Coupon lookup failed")
        return None, TextMessage(
            text="🎟️ 優惠券資料暫時無法讀取，請稍後再試。"
        )

    if coupon is None:
        return None, TextMessage(
            text="這張優惠券資料已更新，請重新開啟優惠券專區。"
        )

    return coupon, None


def handle_coupon_postback(data):
    if data == "coupon_list":
        return create_coupon_list_message()

    if not isinstance(data, str):
        return None

    if data.startswith("coupon_claim&"):
        coupon, error = _get_coupon_or_error(data)
        if error:
            return error
        return _flex(
            f"已領取｜{coupon['title']}",
            create_coupon_bubble(coupon, mode="claimed"),
        )

    if data.startswith("coupon_use&"):
        coupon, error = _get_coupon_or_error(data)
        if error:
            return error
        return _flex(
            f"模擬使用｜{coupon['title']}",
            create_coupon_bubble(coupon, mode="confirm"),
        )

    if data.startswith("coupon_confirm&"):
        coupon, error = _get_coupon_or_error(data)
        if error:
            return error

        return TextMessage(
            text=(
                "✅ 模擬核銷完成\n"
                f"優惠券：{coupon['title']}\n"
                f"內容：{coupon['discount_text']}\n\n"
                "此結果僅供學生專題功能展示，"
                "沒有向任何實體商家進行折抵或交易。"
            )
        )

    return None
