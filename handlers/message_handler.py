
import json

from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    TextMessage,
    FlexMessage,
    FlexContainer
)

from modules.attraction.attraction_service import get_all_attractions
from modules.attraction.flex_message import create_attraction_carousel



def get_ai_reply(text):
    # 5 號的 FAQ / 天氣模組。import 放在函式裡面，萬一它載入失敗，
    # 只有這個功能壞掉，不會讓整個 Bot 一起壞掉。
    try:
        from modules.ai_service import get_reply
        return get_reply(text)
    except Exception as e:
        print(f'get_reply error: {e}')
        return "系統暫時無法回答，請稍後再試一次。"


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
            attractions = get_all_attractions()

            if not attractions:
                reply_text = "目前沒有景點資料，請稍後再試。"
            else:
                carousel = create_attraction_carousel(attractions)

                flex_message = FlexMessage(
                    alt_text="復興區景點導覽",
                    contents=FlexContainer.from_json(
                        json.dumps(carousel, ensure_ascii=False)
                    )
                )

                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[flex_message]
                    )
                )
                return


        elif text == '泰雅文化':
            reply_text = "泰雅文化介紹準備中"
            # TODO: 4 號接手，改成呼叫 modules/culture

        else:
            # 包含選單的「AI 問答」，以及所有其他文字（FAQ、天氣問答）
            reply_text = get_ai_reply(text)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )