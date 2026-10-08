"""Small, explicit keyword classifier, not a generative AI model."""

import unicodedata


def normalize(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return "".join(
        char for char in unicodedata.normalize("NFKC", text).casefold()
        if not char.isspace() and not unicodedata.category(char).startswith("P")
    )


def detect_intent(text: str) -> str:
    value = normalize(text)
    groups = (
        ("weather", ("天氣", "下雨", "氣溫", "降雨", "weather")),
        ("opening_hours", ("營業時間", "開放時間", "幾點開", "幾點關", "有開嗎")),
        ("traffic", ("交通", "公車", "客運", "怎麼去", "如何前往", "路況")),
        ("merchant", ("餐廳", "美食", "民宿", "住宿", "商家", "優惠券")),
        ("attraction", ("景點", "導航")),
        ("culture", ("泰雅", "文化", "部落")),
    )
    for intent, keywords in groups:
        if any(normalize(keyword) in value for keyword in keywords):
            return intent
    return "unknown"
