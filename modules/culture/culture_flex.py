
from modules.culture.culture_service import get_culture_by_id


def create_culture_flex(culture_id):
    """建立泰雅文化 Flex Message 介紹卡片。"""

    culture = get_culture_by_id(culture_id)

    if culture is None:
        return None

    image_url = culture.get("image_url", "").strip()

    hero = None

    # 有 HTTPS 圖片網址時才顯示圖片
    if image_url.startswith("https://"):
        hero = {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover"
        }

    return {
        "type": "bubble",
        "size": "mega",

        # 如果沒有圖片，就不加入 hero
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

        # 新增返回文化主選單按鈕
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "返回文化主選單",
                        "data": "menu_culture",
                        "displayText": "返回泰雅文化選單"
                    }
                }
            ]
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
