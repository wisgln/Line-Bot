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
from modules.location.category_menu import create_category_quick_reply


def handle_location_message(event, configuration):
    latitude = event.message.latitude
    longitude = event.message.longitude

    nearby = find_nearby_attractions(
    latitude,
    longitude,
    limit=5,
    smart_rank=True
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
                contents=FlexContainer.from_dict(carousel),
                quick_reply=create_category_quick_reply(
                    latitude,
                    longitude
                )
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