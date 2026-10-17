from urllib.parse import parse_qs

from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer,
    TextMessage,
)

from modules.location.location_service import find_nearby_attractions
from modules.location.location_flex import create_nearby_carousel
from modules.location.category_menu import (
    CATEGORY_GROUPS,
    create_category_quick_reply,
)


def handle_location_filter(data):
    """
    處理附近景點分類篩選。

    範例：
    location_filter&category=nature&lat=24.95&lng=121.23
    """

    if not data.startswith("location_filter&"):
        return None

    try:
        query_string = data.split("&", 1)[1]
        params = parse_qs(query_string)

        code = params.get("category", ["all"])[0]
        latitude = float(params["lat"][0])
        longitude = float(params["lng"][0])

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("coordinates out of range")

        # 不認得的代號會在這裡出現 KeyError，不會把任意文字印回給使用者
        label, selected_category = CATEGORY_GROUPS[code]

    except (KeyError, ValueError, IndexError):
        return TextMessage(
            text="位置篩選資料有誤，請重新傳送目前位置。"
        )

    nearby = find_nearby_attractions(
        latitude,
        longitude,
        limit=5,
        category=selected_category
    )

    if not nearby:
        return TextMessage(
            text=f"目前找不到「{label}」附近景點。"
        )

    carousel = create_nearby_carousel(nearby)

    return FlexMessage(
        alt_text=f"附近景點｜{label}",
        contents=FlexContainer.from_dict(carousel),
        quick_reply=create_category_quick_reply(
            latitude,
            longitude
        )
    )