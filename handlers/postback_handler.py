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


def get_culture_message(data):
    """
    4 號：泰雅文化模組。
    """

    try:
        from modules.culture.culture_postback import (
            get_culture_postback,
        )

        flex = get_culture_postback(data)

        if flex is None:
            return None

        return FlexMessage(
            alt_text="泰雅文化",
            contents=FlexContainer.from_dict(flex),
        )

    except Exception:
        logger.exception("Culture postback failed")
        return None


def get_location_filter_message(data):
    """
    3 號：LBS 景點分類篩選。
    """

    try:
        from modules.location.location_postback import (
            handle_location_filter,
        )

        return handle_location_filter(data)

    except Exception:
        logger.exception("Location filter postback failed")
        return None


def get_nearby_restaurant_message(data):
    """
    3 號：LBS 附近餐廳推薦。
    """

    try:
        from modules.location.restaurant_postback import (
            handle_nearby_restaurants,
        )

        return handle_nearby_restaurants(data)

    except Exception:
        logger.exception("Nearby restaurant postback failed")
        return None


def handle_postback_event(event, configuration):
    data = event.postback.data

    # =========================
    # 3 號：附近餐廳
    # =========================
    if data.startswith("nearby_restaurants&"):
        message = get_nearby_restaurant_message(data)

        if message is None:
            message = TextMessage(
                text="附近餐廳功能暫時無法使用，請稍後再試。"
            )

    # =========================
    # 3 號：景點分類篩選
    # =========================
    elif data.startswith("location_filter&"):
        message = get_location_filter_message(data)

        if message is None:
            message = TextMessage(
                text="附近景點篩選暫時無法使用，請重新傳送位置。"
            )

    # =========================
    # 4 號：泰雅文化
    # =========================
    elif data == "menu_culture" or data.startswith("culture_"):
        message = get_culture_message(data)

        if message is None:
            message = TextMessage(
                text="泰雅文化內容暫時無法顯示，請稍後再試一次。"
            )

    # =========================
    # 附近景點入口
    # =========================
    elif data == "menu_nearby":
        message = TextMessage(
            text="請傳送你的目前位置，我幫你找附近景點！"
        )

    # =========================
    # 景點導覽
    # =========================
    elif data == "menu_attraction":
        message = TextMessage(
            text="景點導覽功能準備中"
        )

    # =========================
    # AI 問答
    # =========================
    elif data == "menu_ai":
        message = TextMessage(
            text="想問什麼都可以直接打字問我喔！"
        )

    # =========================
    # 未知 postback
    # =========================
    else:
        message = TextMessage(
            text=f"收到 postback: {data}"
        )

    # 回覆 LINE
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[message],
            )
        )