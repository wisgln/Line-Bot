
from modules.culture.culture_service import get_culture_by_id


def create_culture_flex(culture_id):
    """建立泰雅文化 Flex Message 卡片。"""

    culture = get_culture_by_id(culture_id)

    if culture is None:
        return None

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
        }
    }
