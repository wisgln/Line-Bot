"""LINE Flex 優惠券卡片。"""

from modules.coupon.coupon_service import is_expired

DEMO_NOTICE = (
    "⚠️ 中原大學學生專題功能展示用，"
    "非實際商業優惠，不可於實體店家折抵。"
)


def _text(text, *, size="sm", color="#374151", bold=False):
    item = {
        "type": "text",
        "text": str(text),
        "size": size,
        "color": color,
        "wrap": True,
    }
    if bold:
        item["weight"] = "bold"
    return item


def _postback_button(label, data, display_text, *, primary=False):
    button = {
        "type": "button",
        "height": "sm",
        "style": "primary" if primary else "link",
        "action": {
            "type": "postback",
            "label": label,
            "data": data,
            "displayText": display_text,
        },
    }
    if primary:
        button["color"] = "#237A65"
    return button


def create_coupon_bubble(coupon, *, mode="browse"):
    expired = is_expired(coupon)

    body = [
        _text("🎟️ 專題示範優惠券", color="#237A65", bold=True),
        _text(coupon["title"], size="xl", bold=True),
        _text(coupon["category"], size="xs", color="#6B7280"),
        _text(coupon["discount_text"], size="lg", color="#B45309", bold=True),
        _text(coupon["description"]),
        _text(f"展示期限：{coupon['valid_until']}", size="xs"),
        _text(coupon["conditions"], size="xs", color="#6B7280"),
        _text(DEMO_NOTICE, size="xs", color="#B42318", bold=True),
    ]

    footer = []

    if expired:
        body.append(
            _text("此示範券已超過展示期限。", color="#B42318", bold=True)
        )
    elif mode == "browse":
        footer.append(
            _postback_button(
                "領取示範券",
                f"coupon_claim&id={coupon['id']}",
                f"領取：{coupon['title']}",
                primary=True,
            )
        )
    elif mode == "claimed":
        body.insert(
            1,
            _text("✅ 已領取（本次展示）", color="#237A65", bold=True),
        )
        body.append(
            _text(
                "目前版本不會永久保存領取紀錄；"
                "此流程用來展示未來會員優惠券功能。",
                size="xs",
                color="#6B7280",
            )
        )
        footer.append(
            _postback_button(
                "模擬使用",
                f"coupon_use&id={coupon['id']}",
                "模擬使用優惠券",
                primary=True,
            )
        )
    elif mode == "confirm":
        body.insert(
            1,
            _text("準備模擬核銷", color="#B45309", bold=True),
        )
        body.append(
            _text(
                "按下確認只會展示核銷完成畫面，"
                "不會向任何商家送出交易或折抵資料。",
                size="xs",
                color="#6B7280",
            )
        )
        footer.extend([
            _postback_button(
                "確認模擬使用",
                f"coupon_confirm&id={coupon['id']}",
                "確認模擬使用優惠券",
                primary=True,
            ),
            _postback_button(
                "返回優惠券",
                "coupon_list",
                "返回優惠券專區",
            ),
        ])

    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": body,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": footer or [
                _postback_button(
                    "返回優惠券",
                    "coupon_list",
                    "返回優惠券專區",
                )
            ],
        },
    }


def create_coupon_carousel(coupons):
    if not coupons:
        return None

    return {
        "type": "carousel",
        "contents": [
            create_coupon_bubble(coupon, mode="browse")
            for coupon in coupons[:10]
        ],
    }
