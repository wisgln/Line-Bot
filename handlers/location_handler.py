from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)


def handle_location_message(event, configuration):
    latitude = event.message.latitude
    longitude = event.message.longitude

    # TODO: 3 號接手位置，例如：
    # from modules.location.location_service import find_nearby_attractions
    # nearby = find_nearby_attractions(latitude, longitude)
    # 然後把結果做成 Carousel Flex Message 回傳

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(
                        text=f"收到你的位置：緯度 {latitude}, 經度 {longitude}"
                    )
                ]
            )
        )