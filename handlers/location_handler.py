from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer
)

from modules.location.location_service import find_nearby_attractions
from modules.location.location_flex import create_nearby_carousel


def handle_location_message(event, configuration):
    # 使用者傳送的目前位置
    latitude = event.message.latitude
    longitude = event.message.longitude

    # 找出最近 5 個景點
    nearby = find_nearby_attractions(
        latitude,
        longitude,
        limit=5
    )

    if not nearby:
        messages = [
            TextMessage(
                text="目前找不到附近景點，請稍後再試一次。"
            )
        ]

    else:
        carousel = create_nearby_carousel(nearby)

        messages = [
            FlexMessage(
                alt_text="附近景點推薦",
                contents=FlexContainer.from_dict(carousel)
            )
        ]

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages
            )
        )