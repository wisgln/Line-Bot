"""復興好禮：簡潔的 LINE Flex 優惠券及折扣試算卡片。"""

from modules.coupon.coupon_service import calculate_discount, is_expired

GREEN = "#226D57"
INK = "#1F3733"
MUTED = "#718079"
CREAM = "#F1F7F2"
ORANGE = "#B65C20"
NOTICE = "專題展示優惠・非實際商家活動或交易"


def _text(value, size="sm", color=INK, bold=False, **extra):
    item = {
        "type": "text", "text": str(value), "size": size,
        "color": color, "weight": "bold" if bold else "regular", "wrap": True,
    }
    item.update(extra)
    return item


def _button(label, action, cid=None, primary=False):
    data = action if cid is None else f"{action}&id={cid}"
    item = {
        "type": "button", "style": "primary" if primary else "link",
        "height": "sm",
        "action": {
            "type": "postback", "label": label,
            "data": data, "displayText": label,
        },
    }
    if primary:
        item["color"] = GREEN
    return item


def _uri_button(label, url, primary=False):
    button = {
        "type": "button", "style": "primary" if primary else "link",
        "height": "sm", "action": {"type": "uri", "label": label, "uri": url},
    }
    if primary:
        button["color"] = GREEN
    return button


def _bubble(header, body, footer):
    return {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": CREAM,
            "paddingAll": "16px", "contents": [header],
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "paddingAll": "20px", "contents": body,
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "xs",
            "paddingAll": "14px", "contents": footer,
        },
    }


def _note():
    return _text(NOTICE, "xs", MUTED)


def create_coupon_bubble(coupon, mode="browse", shop_url=None):
    """browse/list、detail、claimed、checkout 共用同一份商品及價格資料。"""
    expired = is_expired(coupon)
    cid = coupon["id"]
    price = calculate_discount(coupon)
    tag = _text(f"🎟  復興好禮  /  {coupon['category']}", "xs", GREEN, True)

    if mode == "browse":
        body = [
            _text(coupon["title"], "xl", INK, True),
            _text(coupon["discount_text"], "xxl", ORANGE, True),
            _text(coupon["description"], "sm"),
            _text(f"活動展示至 {coupon['valid_until']}", "xs", MUTED),
            _note(),
        ]
        action = _button("查看優惠", "coupon_detail", cid, True)
    elif mode == "detail":
        body = [
            _text(coupon["title"], "xl", INK, True),
            _text(coupon["discount_text"], "xl", ORANGE, True),
            _text(coupon["description"]),
            _text(f"展示商品：{coupon['product_name']}", "sm"),
            _text(f"適用條件：{coupon['conditions']}", "xs", MUTED),
            _text(f"期限：{coupon['valid_until']}", "xs", MUTED),
            _note(),
        ]
        action = _button("立即領取", "coupon_claim", cid, True)
    elif mode == "claimed":
        body = [
            _text("✓ 已加入優惠券", "md", GREEN, True),
            _text(coupon["title"], "xl", INK, True),
            _text(coupon["discount_text"], "lg", ORANGE, True),
            _text("這次領取僅顯示於目前操作流程。", "xs", MUTED),
            _note(),
        ]
        action = _button("立即使用", "coupon_use", cid, True)
    elif mode == "checkout":
        body = [
            _text("優惠結帳試算", "lg", INK, True),
            _text(coupon["product_name"], "sm"),
            {"type": "separator", "margin": "md"},
            _text(f"商品原價       NT${price['original']:,}", "md"),
            _text(f"優惠折抵       − NT${price['discount']:,}", "md", ORANGE),
            {"type": "separator", "margin": "sm"},
            _text(f"折後總計       NT${price['total']:,}", "xl", GREEN, True),
            _text("這是展示價格，沒有付款或正式訂單。", "xs", MUTED),
        ]
        action = _button("確認試算", "coupon_confirm", cid, True)
    else:
        raise ValueError("Unsupported coupon card mode")

    if expired:
        body.append(_text("此券已超過展示期限", "xs", ORANGE, True))
        action = _button("返回列表", "coupon_list")

    footer = [action]
    if not expired and shop_url and mode == "claimed":
        # 主要按鈕直達手機商品頁；保留 LINE 內試算相容舊卡片與測試。
        footer = [
            _uri_button("立即使用", shop_url, True),
            _button("LINE 內快速試算", "coupon_use", cid),
        ]
    elif not expired and shop_url and mode == "checkout":
        footer = [
            _uri_button("開啟折扣商品頁", shop_url, True),
            _button("確認試算", "coupon_confirm", cid),
        ]
    if mode != "browse":
        footer.append(_button("返回優惠券列表", "coupon_list"))
    return _bubble(tag, body, footer)


def create_coupon_carousel(coupons):
    if not coupons:
        return None
    return {
        "type": "carousel",
        "contents": [create_coupon_bubble(coupon) for coupon in coupons[:10]],
    }
