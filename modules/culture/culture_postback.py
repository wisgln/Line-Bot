
from modules.culture.culture_flex import (
    create_culture_menu,
    create_culture_flex,
)


def get_culture_postback(data):
    """
    處理泰雅文化相關 Postback。

    menu_culture → 文化主題選單
    culture_view:culture001 → 指定文化介紹
    """

    if data == "menu_culture":
        return create_culture_menu()

    if data.startswith("culture_view:"):
        culture_id = data.split(":", 1)[1]
        return create_culture_flex(culture_id)

    return None
