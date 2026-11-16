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


# =====================================
# 4 號：泰雅文化問答文字處理
# =====================================
def get_quiz_reply(data):
    """解析泰雅文化問答資料。"""
    parts = data.split(":")

    if len(parts) != 3:
        return "收不到這個答案，請再試一次。"

    _, quiz_id, user_answer = parts

    from modules.culture.quiz import check_quiz_answer

    result = check_quiz_answer(quiz_id, user_answer)
    lines = [result["message"]]

    if not result["correct"] and result.get("correct_answer"):
        lines.append(
            f"正確答案：{result['correct_answer']}"
        )

    if result.get("explanation"):
        lines.append(
            f"\n說明：{result['explanation']}"
        )

    return "\n".join(lines)


# =====================================
# 4 號：泰雅文化 Flex Message
# =====================================
def get_culture_message(data):
    """處理泰雅文化選單、介紹及問答卡片。"""
    try:
        from modules.culture.culture_postback import (
            get_culture_postback,
        )

        flex = get_culture_postback(data)

        if flex is None:
            return None

        return FlexMessage(
            alt_text="泰雅文化探索",
            contents=FlexContainer.from_dict(flex),
        )

    except Exception:
        logger.exception("Culture postback failed")
        return None


# =====================================
# 3 號：LBS 景點分類篩選
# =====================================
def get_location_filter_message(data):
    """處理景點位置分類篩選。"""
    try:
        from modules.location.location_postback import (
            handle_location_filter,
        )

        return handle_location_filter(data)

    except Exception:
        logger.exception("Location filter postback failed")
        return None


# =====================================
# 3 號：LBS 附近餐廳推薦
# =====================================
def get_nearby_restaurant_message(data):
    """處理附近餐廳推薦。"""
    try:
        from modules.location.restaurant_postback import (
            handle_nearby_restaurants,
        )

        return handle_nearby_restaurants(data)

    except Exception:
        logger.exception("Nearby restaurant postback failed")
        return None


def get_coupon_message(data):
    """專題示範優惠券流程。"""
    try:
        from modules.coupon.coupon_postback import handle_coupon_postback

        return handle_coupon_postback(data)
    except Exception:
        logger.exception("Coupon postback failed")
        return None


# =====================================
# LINE Bot Postback 統一處理入口
# =====================================
def handle_postback_event(event, configuration):
    data = event.postback.data

    # =========================
    # 優惠券專區
    # =========================
    if (
        data == "coupon_list"
        or data.startswith("coupon_detail&")
        or data.startswith("coupon_claim&")
        or data.startswith("coupon_use&")
        or data.startswith("coupon_confirm&")
    ):
        message = get_coupon_message(data)

        if message is None:
            message = TextMessage(
                text="優惠券功能暫時無法使用，請稍後再試。"
            )

    # =========================
    # 3 號：附近餐廳
    # =========================
    elif data.startswith("nearby_restaurants&"):
        message = get_nearby_restaurant_message(data)

        if message is None:
            message = TextMessage(
                text="附近餐廳功能暫時無法使用，請稍後再試。"
            )

    # 3 號：景點分類篩選
    elif data.startswith("location_filter&"):
        message = get_location_filter_message(data)

        if message is None:
            message = TextMessage(
                text="附近景點篩選暫時無法使用，請重新傳送位置。"
            )

    # 4 號：泰雅文化選單、介紹、Quiz 與下一題
    elif data == "menu_culture" or data.startswith("culture_"):
        message = get_culture_message(data)

        if message is None:
            message = TextMessage(
                text="泰雅文化內容暫時無法顯示，請稍後再試一次。"
            )

    # 附近景點入口
    elif data == "menu_nearby":
        message = TextMessage(
            text="請傳送你的目前位置，我幫你找附近景點！"
        )

    # 景點導覽入口
    elif data == "menu_attraction":
        message = TextMessage(
            text="景點導覽功能準備中"
        )

    # AI 問答入口
    elif data == "menu_ai":
        message = TextMessage(
            text="想問什麼都可以直接打字問我喔！"
        )

    # 未知 Postback
    else:
        message = TextMessage(
            text=f"收到 postback: {data}"
        )

    # 統一回覆 LINE
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[message],
            )
        )