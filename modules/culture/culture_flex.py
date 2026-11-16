
from modules.culture.culture_service import (
    get_culture_by_id,
    load_culture_data,
)


def create_culture_flex(culture_id):
    """建立泰雅文化介紹卡片。"""

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
            "contents": [
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "返回泰雅文化選單",
                        "data": "menu_culture",
                        "displayText": "返回泰雅文化選單"
                    }
                }
            ]
        }
    }


def create_culture_menu():
    """顯示八個文化主題及最下方的知識挑戰。"""

    cultures = load_culture_data()

    buttons = []

    # 八個文化主題：點擊後直接顯示介紹
    for culture in cultures:
        buttons.append({
            "type": "button",
            "style": "secondary",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": culture["title"],
                "data": f"culture_view:{culture['id']}",
                "displayText": f"我想了解{culture['title']}"
            }
        })

    # 只有點擊這個按鈕才開始問答
    buttons.append({
        "type": "button",
        "style": "primary",
        "color": "#168A56",
        "height": "sm",
        "action": {
            "type": "postback",
            "label": "泰雅文化知識挑戰",
            "data": "culture_quiz_next:quiz001",
            "displayText": "開始泰雅文化知識挑戰"
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
                    "text": "選擇想認識的泰雅文化主題",
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
