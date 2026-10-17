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
    # 4 號的文化模組：主題選單、主題卡片與 Quiz。
    # import 放在函式裡面，它出錯時不會讓整個 Bot 壞掉。
    try:
        from modules.culture.culture_postback import get_culture_postback

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


def handle_postback_event(event, configuration):
    data = event.postback.data

    if data == 'menu_culture' or data.startswith('culture_'):
        message = get_culture_message(data)
        if message is None:
            message = TextMessage(
                text="泰雅文化內容暫時無法顯示，請稍後再試一次。"
            )

    elif data == 'menu_nearby':
        message = TextMessage(
            text="請傳送你的目前位置，我幫你找附近景點！"
        )

    elif data == 'menu_attraction':
        message = TextMessage(text="景點導覽功能準備中")

    elif data == 'menu_ai':
        message = TextMessage(
            text="想問什麼都可以直接打字問我喔！"
        )

    else:
        message = TextMessage(text=f"收到 postback: {data}")

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[message],
            )
        )