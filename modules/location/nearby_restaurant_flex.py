from modules.merchant.merchant_cards import create_merchant_bubble


def create_nearby_restaurant_carousel(restaurants, limit=5):
    """
    將附近餐廳製作成 LINE Flex Carousel。

    使用既有 merchant 卡片，
    3 號 LBS 模組只額外加入距離資訊。
    """

    if not restaurants:
        return None

    bubbles = []

    for restaurant in restaurants[:limit]:
        # 使用 5 號原本的商家卡片
        bubble = create_merchant_bubble(restaurant)

        distance = restaurant.get("distance")

        # 加入距離資訊
        if distance is not None:
            try:
                distance_text = f"📏 距離：約 {float(distance):.2f} km"
            except (TypeError, ValueError):
                distance_text = None

            if distance_text:
                body_contents = bubble["body"]["contents"]

                # 放在店名下方
                insert_index = min(2, len(body_contents))

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
                    }
                )

        bubbles.append(bubble)

    return {
        "type": "carousel",
        "contents": bubbles,
    }