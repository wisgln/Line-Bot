
from modules.culture.culture_service import get_culture_by_id


# 各文化主題對應的上一層分類
CULTURE_PARENT = {
    "culture001": ("文化小知識", "knowledge"),
    "culture002": ("文化小知識", "knowledge"),
    "culture003": ("文化小知識", "knowledge"),
    "culture004": ("文化小知識", "knowledge"),
    "culture005": ("文化地標", "landmark"),
    "culture006": ("文化地標", "landmark"),
    "culture007": ("傳說故事", "story"),
    "culture008": ("文化地標", "landmark"),
}


def create_culture_flex(culture_id):
    """建立泰雅文化 Flex Message 介紹卡片。"""

    culture = get_culture_by_id(culture_id)

    if culture is None:
        return None

    image_url = culture.get("image_url", "").strip()

    hero = None

    if image_url.startswith("https://"):
        hero = {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover"
        }

    # 找到這張文化卡片所屬的上一層
    parent = CULTURE_PARENT.get(culture_id)
    buttons = []

    if parent:
        parent_title, parent_category = parent

        buttons.append({
            "type": "button",
            "style": "secondary",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": f"返回{parent_title}",
                "data": f"culture_category:{parent_category}",
                "displayText": f"返回{parent_title}"
            }
        })

    # 所有文化卡片都能直接返回主選單
    buttons.append({
        "type": "button",
        "style": "secondary",
        "height": "sm",
        "action": {
            "type": "postback",
            "label": "返回文化主選單",
            "data": "menu_culture",
            "displayText": "返回泰雅文化選單"
        }
    })

    return {
        "type": "bubble",
        "size": "mega",

        **({"hero": hero} if hero else {}),

        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": culture["title"],
                    "weight": "bold",
                    "size": "xl",
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": culture["category"],
                    "size": "sm",
                    "color": "#888888",
                    "wrap": True
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": culture["description"],
                    "size": "md",
                    "wrap": True
                }
            ]
        },

        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": buttons
        }
    }


def create_culture_menu():
    """建立泰雅文化四大分類主選單。"""

    menu_items = [
        ("文化小知識", "culture_category:knowledge"),
        ("文化問答", "culture_quiz_next:quiz001"),
        ("傳說故事", "culture_category:story"),
        ("文化地標", "culture_category:landmark"),
    ]

    buttons = []

    for label, data in menu_items:
        buttons.append({
            "type": "button",
            "style": "secondary",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": label,
                "data": data,
                "displayText": label
            }
        })

    return {
        "type": "bubble",
        "size": "mega",

        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "泰雅文化探索",
                    "weight": "bold",
                    "size": "xl",
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": "一起認識復興區的泰雅文化！",
                    "size": "sm",
                    "color": "#777777",
                    "wrap": True
                }
            ]
        },

        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": buttons
        }
    }
