from urllib.parse import parse_qs

from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer,
    TextMessage,
)

from modules.location.location_service import find_nearby_attractions
from modules.location.location_flex import create_nearby_carousel
from modules.location.category_menu import create_category_quick_reply


def handle_location_filter(data):
    """
    處理附近景點分類篩選。

    範例：
    location_filter&category=自然景觀&lat=24.95&lng=121.23
    """

    if not data.startswith("location_filter&"):
        return None

    try:
        query_string = data.split("&", 1)[1]
        params = parse_qs(query_string)

        category = params.get("category", ["all"])[0]
        latitude = float(params["lat"][0])
        longitude = float(params["lng"][0])

    except (KeyError, ValueError, IndexError):
        return TextMessage(
            text="位置篩選資料有誤，請重新傳送目前位置。"
        )

    # 全部景點時不套分類
    selected_category = None if category == "all" else category

    nearby = find_nearby_attractions(
    latitude,
    longitude,
    limit=5,
    category=selected_category,
    smart_rank=True
)

    if not nearby:
        return TextMessage(
            text=f"目前找不到「{category}」附近景點。"
        )

    carousel = create_nearby_carousel(nearby)

    title = "全部景點" if category == "all" else category

    return FlexMessage(
        alt_text=f"附近景點｜{title}",
        contents=FlexContainer.from_dict(carousel),
        quick_reply=create_category_quick_reply(
            latitude,
            longitude
        )
    )