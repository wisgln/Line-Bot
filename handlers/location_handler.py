from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)

from modules.location.location_service import find_nearby_attractions


def handle_location_message(event, configuration):
    # 取得使用者傳送的位置
    latitude = event.message.latitude
    longitude = event.message.longitude

    # 找出最近 3 個景點
    nearby = find_nearby_attractions(
        latitude,
        longitude,
        limit=3
    )

    # 組合 LINE 回覆文字
    lines = ["📍 你附近的景點推薦"]

    for index, place in enumerate(nearby, start=1):
        lines.append(
            f"\n{index}. {place['name']}"
            f"\n距離：約 {place['distance']} km"
            f"\n地址：{place.get('address', '暫無資料')}"
        )

        if place.get("opening_hours"):
            lines.append(
                f"營業時間：{place['opening_hours']}"
            )

        if place.get("maps_url"):
            lines.append(
                f"🗺️ 導航：{place['maps_url']}"
            )

    reply_text = "\n".join(lines)

    # 回覆 LINE 使用者
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(
                        text=reply_text
                    )
                ]
            )
        )