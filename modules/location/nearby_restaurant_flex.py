from modules.merchant.merchant_cards import (
    create_merchant_bubble,
)


def create_nearby_restaurant_carousel(
    restaurants,
    limit=5,
):
    """
    將附近餐廳製作成 LINE Flex Carousel。
    """

    if not restaurants:
        return None

    bubbles = []

    for restaurant in restaurants[:limit]:

        bubble = create_merchant_bubble(
            restaurant
        )

        distance = restaurant.get(
            "distance"
        )

        if distance is not None:
            try:
                distance_text = (
                    "📏 距離：約 "
                    f"{float(distance):.2f} km"
                )
            except (
                TypeError,
                ValueError,
            ):
                distance_text = None

            if distance_text:
                body_contents = (
                    bubble["body"]["contents"]
                )

                insert_index = min(
                    2,
                    len(body_contents),
                )

                body_contents.insert(
                    insert_index,
                    {
                        "type": "text",
                        "text": distance_text,
                        "size": "sm",
                        "color": "#555555",
                        "weight": "bold",
                        "wrap": True,
                        "margin": "sm",
                    },
                )

        # Google Places 即時結果
        # 必須清楚標示資料來源
        if (
            restaurant.get(
                "source_provider"
            )
            == "google_maps"
        ):
            bubble["body"]["contents"].append(
                {
                    "type": "text",
                    "text": "Google Maps",
                    "size": "xs",
                    "color": "#6B7280",
                    "wrap": True,
                    "margin": "md",
                }
            )

        bubbles.append(bubble)

    return {
        "type": "carousel",
        "contents": bubbles,
    }