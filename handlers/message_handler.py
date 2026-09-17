from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    TextMessage
)


def handle_text_message(event, configuration):
    text = event.message.text

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if text == 'postback':
            buttons_template = ButtonsTemplate(
                title='Postback Sample',
                text='Postback Actions',
                actions=[
                    PostbackAction(
                        label='Postback Action',
                        text='Postback Action Button Clicked!',
                        data='postback'
                    ),
                ]
            )
            template_message = TemplateMessage(
                alt_text='Postback Sample',
                template=buttons_template
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[template_message]
                )
            )
            return

        if text == '附近景點推薦':
            reply_text = "請傳送你的目前位置，我幫你找附近景點！"
            # TODO: 3 號接手，改成呼叫 modules/location

        elif text == '景點導覽':
            reply_text = "景點導覽功能準備中"
            # TODO: 2 號接手，改成呼叫 modules/attraction 回傳景點 Flex Message

        elif text == '泰雅文化':
            reply_text = "泰雅文化介紹準備中"
            # TODO: 4 號接手，改成呼叫 modules/culture

        elif text == 'AI 問答':
            reply_text = "想問什麼都可以直接打字問我喔！"
            # TODO: 5 號接手，改成呼叫 modules/ai_service

        else:
            # 尚未定義的文字，先 echo 回去，確認串接正常
            reply_text = text

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )