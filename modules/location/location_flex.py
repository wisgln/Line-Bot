from modules.attraction.flex_message import create_attraction_bubble


def create_nearby_carousel(attractions):
    """
    將附近景點製作成 LINE Flex Carousel。
    使用 2 號既有的景點卡片，再加入距離資訊。
    """

    if not attractions:
        return None

    bubbles = []

    for attraction in attractions[:5]:
        # 使用 2 號既有的單一景點卡片
        bubble = create_attraction_bubble(attraction)

        distance = attraction.get("distance")

        # 加入 LBS 距離資訊
        if distance is not None:
            bubble["body"]["contents"].insert(
                2,
                {
                    "type": "text",
                    "text": f"📍 距離：約 {distance:.2f} km",
                    "size": "sm",
                    "color": "#555555",
                    "weight": "bold",
                    "wrap": True,
                    "margin": "md"
                }
            )

        bubbles.append(bubble)

    return {
        "type": "carousel",
        "contents": bubbles
    }