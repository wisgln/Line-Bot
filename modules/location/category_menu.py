from linebot.v3.messaging import (
    QuickReply,
    QuickReplyItem,
    PostbackAction,
)


CATEGORIES = [
    ("全部", "all"),
    ("自然景觀", "自然景觀"),
    ("歷史文化", "歷史文化"),
    ("部落文化", "部落文化"),
]


def create_category_quick_reply(latitude, longitude):
    items = []

    for label, category in CATEGORIES:
        data = (
            f"location_filter"
            f"&category={category}"
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

    return QuickReply(items=items)