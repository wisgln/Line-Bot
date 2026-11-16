
from modules.culture.culture_flex import (
    create_culture_menu,
    create_culture_flex,
)
from modules.culture.culture_service import load_culture_data
from modules.culture.quiz import (
    create_quiz_flex,
    create_quiz_result_flex,
)


# 四大分類對應的文化資料
CULTURE_CATEGORIES = {
    "knowledge": [
        "culture001",
        "culture002",
        "culture003",
        "culture004",
    ],
    "story": [
        "culture007",
    ],
    "landmark": [
        "culture005",
        "culture006",
        "culture008",
    ],
}


def create_culture_category_menu(category):
    """依分類建立文化主題選單。"""

    culture_ids = CULTURE_CATEGORIES.get(category)

    if culture_ids is None:
        return None

    cultures = load_culture_data()

    selected = [
        culture
        for culture in cultures
        if culture["id"] in culture_ids
    ]

    buttons = []

    for culture in selected:
        buttons.append({
            "type": "button",
            "style": "secondary",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": culture["title"],
                "data": f"culture_view:{culture['id']}",
                "displayText": culture["title"],
            },
        })

    category_titles = {
        "knowledge": "泰雅文化小知識",
        "story": "泰雅族傳說故事",
        "landmark": "泰雅文化地標",
    }

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
                    "text": category_titles.get(category, "泰雅文化"),
                    "weight": "bold",
                    "size": "xl",
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": "請選擇想了解的主題",
                    "size": "sm",
                    "color": "#777777",
                    "wrap": True,
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": buttons + [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "返回文化主選單",
                        "data": "menu_culture",
                        "displayText": "返回泰雅文化選單",
                    },
                }
            ],
        },
    }


def get_culture_postback(data):
    """處理所有泰雅文化 Postback。"""

    # 文化主選單
    if data == "menu_culture":
        return create_culture_menu()

    # 文化分類選單
    if data.startswith("culture_category:"):
        category = data.split(":", 1)[1]
        return create_culture_category_menu(category)

    # 文化介紹
    if data.startswith("culture_view:"):
        culture_id = data.split(":", 1)[1]
        return create_culture_flex(culture_id)

    # Quiz 下一題
    if data.startswith("culture_quiz_next:"):
        quiz_id = data.split(":", 1)[1]
        return create_quiz_flex(quiz_id)

    # Quiz 答題結果
    if data.startswith("culture_quiz:"):
        parts = data.split(":")

        if len(parts) != 3:
            return None

        _, quiz_id, user_answer = parts

        return create_quiz_result_flex(quiz_id, user_answer)

    return None
