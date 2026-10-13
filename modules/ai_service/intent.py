"""以明確關鍵字辨識旅遊問題，非生成式 AI 模型。"""

import unicodedata


def normalize(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    return "".join(
        char
        for char in unicodedata.normalize("NFKC", text).casefold()
        if not char.isspace()
        and not unicodedata.category(char).startswith("P")
    )


FOOD_KEYWORDS = (
    "餐廳",
    "美食",
    "小吃",
    "肚子餓",
    "餓了",
    "吃什麼",
    "吃甚麼",
    "吃點什麼",
    "有什麼吃",
    "有甚麼吃",
    "有什麼能吃",
    "有甚麼能吃",
    "哪裡吃",
    "哪裡有吃",
    "想吃",
    "找吃的",
    "吃飯",
    "用餐",
    "早餐",
    "午餐",
    "晚餐",
)

LODGING_KEYWORDS = (
    "民宿",
    "住宿",
    "住一晚",
    "住兩晚",
    "住哪",
    "住在",
    "過夜",
    "找房間",
    "訂房",
)

NEARBY_KEYWORDS = (
    "附近",
    "離我近",
    "離我最近",
    "周邊",
    "週邊",
    "旁邊",
)

TRAFFIC_KEYWORDS = (
    "交通",
    "公車",
    "客運",
    "班次",
    "時刻表",
    "末班車",
    "首班車",
    "到站",
    "路況",
    "道路管制",
    "封路",
    "通車",
    "怎麼去",
    "怎麼到",
    "怎麼走",
    "如何前往",
    "如何到",
    "怎麼搭",
    "怎樣去",
    "怎樣搭",
    "如何搭",
    "搭車",
    "搭乘",
    "開車",
    "停車",
    "搭什麼車",
    "搭甚麼車",
    "坐什麼車",
    "坐甚麼車",
    "坐車",
)


def contains_any(value, keywords):
    return any(normalize(word) in value for word in keywords)


def detect_intent(text: str) -> str:
    value = normalize(text)

    # 優惠券不是餐廳或住宿清單。
    if "優惠券" in value:
        return "coupon"

    # 明確交通問法優先，例如「去餐廳要搭什麼車」。
    if contains_any(value, TRAFFIC_KEYWORDS):
        return "traffic"

    if contains_any(
        value,
        ("天氣", "下雨", "氣溫", "降雨", "weather"),
    ):
        return "weather"

    food = contains_any(value, FOOD_KEYWORDS)
    lodging = contains_any(value, LODGING_KEYWORDS)
    nearby = contains_any(value, NEARBY_KEYWORDS)

    # 附近商家查詢需要位置，不直接回傳全部店家。
    if nearby and (food or lodging or "商家" in value):
        return "nearby_merchant"

    # 明確詢問開放時間時，保留原有意圖。
    if contains_any(
        value,
        ("營業時間", "開放時間", "幾點開", "幾點關", "有開嗎"),
    ):
        return "opening_hours"

    if lodging:
        return "lodging"

    if food or "商家" in value:
        return "merchant"

    if contains_any(value, ("景點", "導航")):
        return "attraction"

    if contains_any(value, ("泰雅", "文化", "部落")):
        return "culture"

    return "unknown"