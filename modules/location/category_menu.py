from linebot.v3.messaging import (
    QuickReply,
    QuickReplyItem,
    PostbackAction,
)


# 代號 → (按鈕文字, 包含的資料類別)
# None 代表全部景點
CATEGORY_GROUPS = {
    "all": (
        "全部景點",
        None,
    ),
    "nature": (
        "自然與步道",
        (
            "自然景觀",
            "生態步道",
            "橋梁景觀",
        ),
    ),
    "history": (
        "歷史文化",
        (
            "歷史文化",
        ),
    ),
    "tribe": (
        "部落文化",
        (
            "部落文化",
        ),
    ),
    "leisure": (
        "休閒體驗",
        (
            "休閒",
            "戶外活動",
            "商圈休閒",
        ),
    ),
}


def create_category_quick_reply(
    latitude,
    longitude,
):
    """
    建立附近景點分類與附近餐廳 Quick Reply。
    """

    items = []

    # 景點分類
    for code, (label, _) in CATEGORY_GROUPS.items():
        data = (
            f"location_filter"
            f"&category={code}"
            f"&lat={latitude}"
            f"&lng={longitude}"
        )

        items.append(
            QuickReplyItem(
                action=PostbackAction(
                    label=label,
                    data=data,
                    display_text=f"篩選：{label}",
                )
            )
        )

    # 附近餐廳
    items.append(
        QuickReplyItem(
            action=PostbackAction(
                label="附近餐廳",
                data=(
                    f"nearby_restaurants"
                    f"&lat={latitude}"
                    f"&lng={longitude}"
                ),
                display_text="附近餐廳",
            )
        )
    )

    return QuickReply(
        items=items
    )