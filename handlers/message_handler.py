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


def get_ai_reply(text, session_id=None):
    # 5 號的 FAQ / 天氣模組。import 放在函式裡面，萬一它載入失敗，
    # 只有這個功能壞掉，不會讓整個 Bot 一起壞掉。
    try:
        from modules.ai_service import get_reply
        return get_reply(text, session_id=session_id)
    except Exception as e:
        print(f'get_reply error: {e}')
        return "系統暫時無法回答，請稍後再試一次。"


def get_culture_messages():
    # 4 號的文化模組：文化介紹卡片 + Quiz 題目卡片。
    # import 放在函式裡面，它出錯時不會讓整個 Bot 壞掉
    try:
        from modules.culture.culture_flex import create_culture_flex
        from modules.culture.quiz import create_quiz_flex

        messages = []

        culture_flex = create_culture_flex('culture001')
        if culture_flex:
            messages.append(
                FlexMessage(
                    alt_text='泰雅文化介紹',
                    contents=FlexContainer.from_dict(culture_flex)
                )
            )

        quiz_flex = create_quiz_flex('quiz001')
        if quiz_flex:
            messages.append(
                FlexMessage(
                    alt_text='泰雅文化知識挑戰',
                    contents=FlexContainer.from_dict(quiz_flex)
                )
            )

        return messages
    except Exception as e:
        print(f'culture error: {e}')
        return []


def get_attraction_message():
    # 2 號的景點導覽模組。import 放在函式裡面，它出錯時不會讓整個 Bot 壞掉。
    # LINE 的 Flex 輪播最多 12 張，所以目前只取前 12 筆。
    try:
        from modules.attraction.attraction_service import get_all_attractions
        from modules.attraction.flex_message import create_attraction_carousel

        attractions = get_all_attractions()[:12]
        if not attractions:
            return None

        carousel = create_attraction_carousel(attractions)
        return FlexMessage(
            alt_text='復興區景點導覽',
            contents=FlexContainer.from_json(
                json.dumps(carousel, ensure_ascii=False)
            )
        )
    except Exception as e:
        print(f'attraction error: {e}')
        return None


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
            reply_text = "景點導覽暫時無法顯示，請稍後再試一次。"
            attraction_message = get_attraction_message()

            if attraction_message:
                try:
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[attraction_message]
                        )
                    )
                    return
                except Exception as e:
                    print(f'attraction reply error: {e}')

        elif text == '泰雅文化':
            reply_text = "泰雅文化介紹暫時無法顯示，請稍後再試一次。"
            culture_messages = get_culture_messages()

            if culture_messages:
                try:
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=culture_messages
                        )
                    )
                    return
                except Exception as e:
                    print(f'culture reply error: {e}')

        else:
            # 包含選單的「AI 問答」，以及所有其他文字（FAQ、天氣問答）
            # 群組、聊天室與私人對話分開，同時區分每位使用者。
            source = event.source
            user_id = getattr(source, 'user_id', None)
            scope = getattr(source, 'group_id', None) or getattr(source, 'room_id', None) or 'private'
            session_id = f'{scope}:{user_id}' if user_id else None
            reply_text = get_ai_reply(text, session_id=session_id)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
