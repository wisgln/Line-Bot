"""優惠券領取與折扣結帳試算：全程不建立實際付款或商家訂單。"""

import logging
from urllib.parse import parse_qs

from linebot.v3.messaging import FlexContainer, FlexMessage, TextMessage

from modules.coupon.coupon_flex import create_coupon_bubble, create_coupon_carousel
from modules.coupon.coupon_links import get_coupon_shop_url
from modules.coupon.coupon_service import (
    calculate_discount, get_coupon, is_expired, load_coupons,
)

logger = logging.getLogger(__name__)


def _coupon_id(data):
    if not isinstance(data, str) or "&" not in data:
        return None
    try:
        return parse_qs(data.split("&", 1)[1])["id"][0]
    except (KeyError, IndexError):
        return None


def _flex(alt_text, contents):
    return FlexMessage(
        alt_text=alt_text[:100],
        contents=FlexContainer.from_dict(contents),
    )


def create_coupon_list_message():
    try:
        carousel = create_coupon_carousel(load_coupons())
    except (OSError, ValueError):
        logger.exception("Coupon data unavailable")
        return TextMessage(text="優惠券資料暫時無法讀取，請稍後再試。")

    if not carousel:
        return TextMessage(text="目前沒有優惠券可瀏覽。")
    return _flex("復興好禮｜優惠券專區（專題展示）", carousel)


def _coupon_or_message(data):
    cid = _coupon_id(data)
    if not cid:
        return None, TextMessage(text="優惠券連結有誤，請重新開啟優惠券專區。")
    try:
        coupon = get_coupon(cid)
    except (OSError, ValueError):
        logger.exception("Coupon lookup failed")
        return None, TextMessage(text="優惠券資料暫時無法讀取，請稍後再試。")
    if coupon is None:
        return None, TextMessage(text="這張優惠券資料已更新，請重新開啟優惠券專區。")
    if is_expired(coupon):
        return None, TextMessage(text="這張優惠券已過展示期限，可返回優惠券專區看看其他選項。")
    return coupon, None


def handle_coupon_postback(data):
    if data == "coupon_list":
        return create_coupon_list_message()

    if not isinstance(data, str):
        return None

    for prefix, mode, title in (
        ("coupon_detail&", "detail", "優惠詳情"),
        ("coupon_claim&", "claimed", "已領取"),
        ("coupon_use&", "checkout", "優惠結帳試算"),
    ):
        if data.startswith(prefix):
            coupon, error = _coupon_or_message(data)
            if error is not None:
                return error
            return _flex(
                f"{title}｜{coupon['title']}",
                create_coupon_bubble(
                    coupon, mode=mode,
                    shop_url=get_coupon_shop_url(coupon["id"]),
                ),
            )

    if data.startswith("coupon_confirm&"):
        coupon, error = _coupon_or_message(data)
        if error is not None:
            return error
        price = calculate_discount(coupon)
        return TextMessage(
            text=(
                "✅ 折扣試算完成\n"
                f"商品：{coupon['product_name']}\n"
                f"原價：NT${price['original']:,}\n"
                f"折扣：−NT${price['discount']:,}\n"
                f"折後總計：NT${price['total']:,}\n\n"
                "本次為專題展示，不會產生實際訂單或付款，"
                "亦未向任何實體商家核銷。"
            )
        )

    return None
