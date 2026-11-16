from urllib.parse import parse_qs

from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer,
    TextMessage,
)

from modules.location.merchant_location_service import (
    find_nearby_merchants,
)
from modules.location.nearby_restaurant_flex import (
    create_nearby_restaurant_carousel,
)
from modules.location.category_menu import (
    create_category_quick_reply,
)


def handle_nearby_restaurants(data):
    """
    處理附近餐廳查詢。

    Postback 範例：
    nearby_restaurants&lat=24.95&lng=121.23
    """

    if not data.startswith("nearby_restaurants&"):
        return None

    try:
        query_string = data.split("&", 1)[1]
        params = parse_qs(query_string)

        latitude = float(params["lat"][0])
        longitude = float(params["lng"][0])

    except (KeyError, ValueError, IndexError):
        return TextMessage(
            text="位置資料有誤，請重新傳送目前位置。"
        )

    restaurants = find_nearby_merchants(
        latitude,
        longitude,
        limit=5,
        category="餐廳",
    )

    if not restaurants:
        return TextMessage(
            text=(
                "目前尚未取得餐廳定位資料，"
                "附近餐廳功能正在建置中。"
            )
        )

    carousel = create_nearby_restaurant_carousel(
        restaurants
    )

    if carousel is None:
        return TextMessage(
            text="目前找不到附近餐廳，請稍後再試一次。"
        )

    return FlexMessage(
        alt_text="附近餐廳推薦",
        contents=FlexContainer.from_dict(carousel),
        quick_reply=create_category_quick_reply(
            latitude,
            longitude,
        ),
    )