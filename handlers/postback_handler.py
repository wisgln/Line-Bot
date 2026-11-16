
import json

from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer
)

from modules.attraction.attraction_service import get_all_attractions
from modules.attraction.flex_message import create_attraction_carousel


def get_quiz_reply(data):
    # data 格式：culture_quiz:題目ID:選項
    parts = data.split(':')

    if len(parts) != 3:
        return "收不到這個答案，請再試一次。"

    _, quiz_id, user_answer = parts

    # 4 號組員的文化測驗模組
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

    reply_message = None

    # 4號：泰雅文化測驗
    if data.startswith('culture_quiz:'):
        try:
            reply_text = get_quiz_reply(data)
        except Exception as e:
            print(f'culture quiz error: {e}')
            reply_text = "題目暫時無法判斷，請稍後再試一次。"

        reply_message = TextMessage(text=reply_text)

    # 3號：附近景點推薦
    elif data == 'menu_nearby':
        reply_message = TextMessage(
            text="請傳送你的目前位置，我幫你找附近景點！"
        )

    # 2號：景點導覽主選單
    elif data == 'menu_attraction':
        attractions = get_all_attractions()
        carousel = create_attraction_carousel(attractions, page=1)

        if carousel:
            reply_message = FlexMessage(
                alt_text="復興區景點導覽 - 第1頁",
                contents=FlexContainer.from_json(
                    json.dumps(carousel, ensure_ascii=False)
                )
            )
        else:
            reply_message = TextMessage(
                text="目前沒有景點資料。"
            )

    # 2號：景點上一頁、下一頁
    elif data.startswith('attraction_page='):
        try:
            page = int(data.split('=', 1)[1])

            attractions = get_all_attractions()
            total_pages = (len(attractions) + 9) // 10

            if page < 1 or page > total_pages:
                reply_message = TextMessage(
                    text="頁碼錯誤，請重新選擇景點導覽。"
                )
            else:
                carousel = create_attraction_carousel(
                    attractions, page=page
                )

                reply_message = FlexMessage(
                    alt_text=f"復興區景點導覽 - 第{page}頁",
                    contents=FlexContainer.from_json(
                        json.dumps(carousel, ensure_ascii=False)
                    )
                )

        except (ValueError, IndexError):
            reply_message = TextMessage(
                text="頁碼錯誤，請重新選擇景點導覽。"
            )

    # 4號：泰雅文化主選單
    elif data == 'menu_culture':
        reply_message = TextMessage(
            text="泰雅文化介紹準備中"
        )

    # 5號：AI 問答
    elif data == 'menu_ai':
        reply_message = TextMessage(
            text="想問什麼都可以直接打字問我喔！"
        )

    else:
        reply_message = TextMessage(
            text=f"收到 postback: {data}"
        )

    # 統一回覆 LINE 訊息
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message]
            )
        )
