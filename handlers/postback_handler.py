from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)


def handle_postback_event(event, configuration):
    data = event.postback.data

    if data == 'menu_nearby':
        reply_text = "請傳送你的目前位置，我幫你找附近景點！"
        # TODO: 3 號之後可能改成直接觸發 LINE 的位置分享請求

    elif data == 'menu_attraction':
        reply_text = "景點導覽功能準備中"
        # TODO: 2 號接手，改成呼叫 modules/attraction 回傳景點 Flex Message

    elif data == 'menu_culture':
        reply_text = "泰雅文化介紹準備中"
        # TODO: 4 號接手，改成呼叫 modules/culture

    elif data == 'menu_ai':
        reply_text = "想問什麼都可以直接打字問我喔！"
        # TODO: 5 號接手，可視需求調整成更明確的導引文字

    else:
        reply_text = f"收到 postback: {data}"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )