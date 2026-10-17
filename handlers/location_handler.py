import logging

from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
)


logger = logging.getLogger(__name__)


def get_nearby(latitude, longitude):
    # 3 號的定位模組。import 放在函式裡面，它出錯時不會讓整個 Bot 壞掉。
    try:
        from modules.location.location_service import find_nearby_attractions

        return find_nearby_attractions(latitude, longitude, limit=5)
    except Exception:
        logger.exception("Nearby search failed")
        return None


def make_carousel_message(nearby):
    try:
        from modules.location.location_flex import create_nearby_carousel

        carousel = create_nearby_carousel(nearby)
        if not carousel:
            return None

        return FlexMessage(
            alt_text="附近景點推薦",
            contents=FlexContainer.from_dict(carousel),
        )
    except Exception:
        logger.exception("Nearby carousel failed")
        return None


def make_text_message(nearby):
    # 卡片失敗時的備案：原本的文字列表。
    lines = ["📍 你附近的景點推薦"]

    for index, place in enumerate(nearby, start=1):
        lines.append(
            f"\n{index}. {place['name']}"
            f"\n距離：約 {place['distance']} km"
            f"\n地址：{place.get('address', '暫無資料')}"
        )

        if place.get("opening_hours"):
            lines.append(f"營業時間：{place['opening_hours']}")

        if place.get("phone"):
            lines.append(f"電話：{place['phone']}")

        if place.get("maps_url"):
            lines.append(f"🗺️ 導航：{place['maps_url']}")

    return TextMessage(text="\n".join(lines))


def handle_location_message(event, configuration):
    latitude = event.message.latitude
    longitude = event.message.longitude

    nearby = get_nearby(latitude, longitude)

    if nearby is None:
        messages = [
            TextMessage(text="附近景點暫時無法查詢，請稍後再試一次。")
        ]
    elif not nearby:
        messages = [
            TextMessage(text="目前找不到附近景點，請稍後再試一次。")
        ]
    else:
        message = make_carousel_message(nearby)

        if message is None:
            try:
                message = make_text_message(nearby)
            except Exception:
                logger.exception("Nearby text failed")
                message = TextMessage(
                    text="附近景點暫時無法顯示，請稍後再試一次。"
                )

        messages = [message]

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=messages,
                )
            )
        except Exception:
            # 卡片送出時被 LINE 拒絕，改用文字列表再送一次。
            logger.exception("Nearby reply failed")

            if not nearby:
                raise

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[make_text_message(nearby)],
                )
            )