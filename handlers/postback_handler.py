
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer
)



def get_quiz_reply(data):
    # data 格式：culture_quiz:題目ID:選項，例如 culture_quiz:quiz001:B
    parts = data.split(':')
    if len(parts) != 3:
        return "收不到這個答案，請再試一次。"

    _, quiz_id, user_answer = parts

    # 4 號的模組。import 放在函式裡面，它出錯時不會讓整個 Bot 壞掉
    from modules.culture.quiz import check_quiz_answer
    result = check_quiz_answer(quiz_id, user_answer)

    lines = [result["message"]]

    if not result["correct"] and result.get("correct_answer"):
        lines.append(f"正確答案是 {result['correct_answer']}")

    if result.get("explanation"):
        lines.append(f"\n💡 {result['explanation']}")

    return "\n".join(lines)



def handle_postback_event(event, configuration):
    data = event.postback.data

    if (
        data == "menu_culture"
        or data.startswith("culture_view:")
        or data.startswith("culture_quiz:")
        or data.startswith("culture_quiz_next:")
    ):
        try:
            from modules.culture.culture_postback import get_culture_postback

            culture_flex = get_culture_postback(data)

            if culture_flex is not None:
                reply_message = FlexMessage(
                    alt_text="泰雅文化探索",
                    contents=FlexContainer.from_dict(culture_flex)
                )
            else:
                reply_message = TextMessage(
                    text="找不到相關文化內容，請重新選擇。"
                )

        except Exception as e:
            print(f"culture postback error: {e}")
            reply_message = TextMessage(
                text="泰雅文化功能暫時無法使用，請稍後再試。"
            )

    elif data == "menu_nearby":
        reply_message = TextMessage(
            text="請傳送你的目前位置，我幫你找附近景點！"
        )

    elif data == "menu_attraction":
        reply_message = TextMessage(
            text="景點導覽功能準備中"
        )

    elif data == "menu_ai":
        reply_message = TextMessage(
            text="想問什麼都可以直接打字問我喔！"
        )

    else:
        reply_message = TextMessage(
            text=f"收到 postback: {data}"
        )

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message]
            )
        )
