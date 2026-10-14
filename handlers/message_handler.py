"""文字訊息、商家字卡、景點字卡、行程站次與文化功能。"""

import logging
import re
import unicodedata

from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    TextMessage,
    FlexMessage,
    FlexContainer,
)


logger = logging.getLogger(__name__)


def get_ai_reply(text, session_id=None):
    try:
        from modules.ai_service import get_reply

        return get_reply(text, session_id=session_id)
    except Exception:
        logger.error("AI reply failed")
        return "🌿 暫時無法回答，請稍後再試一次。"


def get_culture_messages():
    try:
        from modules.culture.culture_flex import create_culture_flex
        from modules.culture.quiz import create_quiz_flex

        messages = []

        for data, title in (
            (create_culture_flex("culture001"), "泰雅文化介紹"),
            (create_quiz_flex("quiz001"), "泰雅文化知識挑戰"),
        ):
            if data:
                messages.append(
                    FlexMessage(
                        alt_text=title,
                        contents=FlexContainer.from_dict(data),
                    )
                )

        return messages
    except Exception:
        logger.error("Culture cards failed")
        return []


def make_attraction_message(attraction):
    from modules.attraction.flex_message import create_attraction_bubble

    return FlexMessage(
        alt_text=f"景點介紹｜{attraction['name']}"[:100],
        contents=FlexContainer.from_dict(
            create_attraction_bubble(attraction)
        ),
    )


def get_attraction_message():
    try:
        from modules.attraction.attraction_service import get_all_attractions
        from modules.attraction.flex_message import create_attraction_carousel

        attractions = get_all_attractions()[:12]
        if not attractions:
            return None

        return FlexMessage(
            alt_text="復興區景點導覽",
            contents=FlexContainer.from_dict(
                create_attraction_carousel(attractions)
            ),
        )
    except Exception:
        logger.error("Attraction carousel failed")
        return None


def normalize_card_query(text):
    return "".join(
        char
        for char in unicodedata.normalize("NFKC", text).casefold()
        if not char.isspace()
        and not unicodedata.category(char).startswith("P")
    )


def extract_attraction_keyword(text):
    query = normalize_card_query(text)

    for prefix in (
        "可以介紹一下", "可以介紹", "請介紹一下", "幫我介紹",
        "我想了解", "我想看", "介紹一下", "請介紹",
        "介紹", "查詢", "查看", "看看", "看",
    ):
        if query.startswith(prefix):
            query = query[len(prefix):]
            break

    for suffix in (
        "的詳細介紹", "的介紹", "的字卡", "的卡片", "的地圖",
        "的導航", "詳細介紹", "介紹", "字卡", "卡片", "地圖", "導航",
    ):
        if query.endswith(suffix):
            query = query[:-len(suffix)]
            break

    return query


def get_named_attraction_message(text):
    try:
        from modules.attraction.attraction_service import get_all_attractions
        from modules.ai_service.emergency import get_emergency_reply
        from modules.ai_service.gemini_reply import is_planning

        if get_emergency_reply(text) is not None or is_planning(text):
            return None

        attractions = [
            item for item in get_all_attractions()
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and item["name"].strip()
        ]

        query = normalize_card_query(text)
        matches = [
            item for item in attractions
            if normalize_card_query(item["name"]) == query
        ]

        if not matches:
            keyword = extract_attraction_keyword(text)
            if len(keyword) < 2:
                return None

            matches = [
                item for item in attractions
                if normalize_card_query(item["name"]) == keyword
            ]

            if not matches:
                matches = [
                    item for item in attractions
                    if keyword in normalize_card_query(item["name"])
                ]

        if not matches:
            return None

        if len(matches) > 1:
            names = list(dict.fromkeys(item["name"] for item in matches))
            lines = ["📍 找到幾個符合的景點：", ""]
            lines.extend(f"・{name}" for name in names[:8])
            lines.extend(["", "請輸入完整景點名稱，我幫你開啟字卡。"])
            return TextMessage(text="\n".join(lines))

        return make_attraction_message(matches[0])

    except Exception:
        logger.error("Named attraction card failed")
        return None


def get_merchant_card_message(text):
    """商家選單、分類、翻頁和完整店名字卡。"""
    try:
        from modules.ai_service.emergency import get_emergency_reply
        from modules.merchant.merchant_cards import get_merchant_message

        # 求救問題交由原本的緊急聯絡模組優先處理。
        if get_emergency_reply(text) is not None:
            return None

        return get_merchant_message(text)

    except Exception:
        logger.error("Merchant cards failed")
        # 字卡失敗時，交回原本的文字查詢。
        return None


def parse_stop_number(text):
    """只辨識查看指令，不攔截『第二站換掉』或求救問題。"""
    query = normalize_card_query(text)
    match = re.fullmatch(
        r"(?:請幫我看|幫我看|請查看|請看|我想看|查看|看看|看)?"
        r"第([0-9]{1,2}|[一二三四五六七八九十兩]{1,3})站"
        r"(?:的)?(?:詳情|介紹|字卡|卡片|地圖|導航)?",
        query,
    )

    if not match:
        return None

    value = match.group(1)
    numbers = {
        "一": 1,
        "二": 2,
        "兩": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "十一": 11,
        "十二": 12,
    }

    return int(value) if value.isdigit() else numbers.get(value)


def get_itinerary_message(text, session_id):
    """依已保存的行程順序，顯示指定站次的景點字卡。"""
    number = parse_stop_number(text)
    if number is None:
        return None

    try:
        from modules.ai_service.gemini_reply import get_saved_stops
        from modules.attraction.attraction_service import get_all_attractions

        stops = get_saved_stops(session_id)

        if not stops:
            return TextMessage(
                text=(
                    "🌿 目前沒有可查看的行程，或對話記憶已過期。\n"
                    "請先安排新行程，也可以直接輸入景點名稱。"
                )
            )

        if not 1 <= number <= len(stops):
            return TextMessage(
                text=f"📍 目前行程共有{len(stops)}站，請選擇其中一站。"
            )

        stop = stops[number - 1]

        if stop["kind"] != "attraction":
            lines = [f"📍 第{number}站｜{stop['name']}"]
            if stop.get("note"):
                lines.append(stop["note"])
            lines.append("這站是用餐、住宿或其他安排，沒有景點字卡。")
            return TextMessage(text="\n".join(lines))

        matches = [
            item for item in get_all_attractions()
            if isinstance(item, dict)
            and str(item.get("id")) == stop["id"]
        ]

        # 名稱改變或 id 重複時，不開啟可能對錯店家的卡片。
        if len(matches) != 1 or matches[0].get("name") != stop["name"]:
            return TextMessage(
                text="🌿 這站的景點資料已異動，請重新查詢景點或調整行程。"
            )

        return make_attraction_message(matches[0])

    except Exception:
        logger.error("Itinerary card failed")
        return TextMessage(
            text="🌿 這站的資料暫時無法顯示，請稍後再試。"
        )


def get_session_id(event):
    source = event.source
    user_id = getattr(source, "user_id", None)

    if not user_id:
        return None

    scope = (
        getattr(source, "group_id", None)
        or getattr(source, "room_id", None)
        or "private"
    )
    return f"{scope}:{user_id}"


def handle_text_message(event, configuration):
    text = event.message.text.strip()
    session_id = get_session_id(event)

    if text == "postback":
        messages = [
            TemplateMessage(
                alt_text="Postback Sample",
                template=ButtonsTemplate(
                    title="Postback Sample",
                    text="Postback Actions",
                    actions=[
                        PostbackAction(
                            label="Postback Action",
                            text="Postback Action Button Clicked!",
                            data="postback",
                        )
                    ],
                ),
            )
        ]

    elif text == "附近景點推薦":
        messages = [
            TextMessage(
                text="📍 請傳送你的目前位置，我幫你找附近景點！"
            )
        ]

    elif text == "景點導覽":
        message = get_attraction_message()
        messages = [
            message if message is not None
            else TextMessage(
                text="🌿 景點導覽暫時無法顯示，請稍後再試。"
            )
        ]

    elif text == "泰雅文化":
        messages = get_culture_messages()
        if not messages:
            messages = [
                TextMessage(
                    text="🌿 文化介紹暫時無法顯示，請稍後再試。"
                )
            ]

    else:
        # 明確的「看第幾站」保留原有行程順序。
        message = get_itinerary_message(text, session_id)

        # 商家模組只接明確選單、翻頁及完整店名。
        if message is None:
            message = get_merchant_card_message(text)

        if message is None:
            message = get_named_attraction_message(text)

        # 其他問題交給原本的 FAQ、天氣、緊急聯絡或 AI。
        if message is None:
            message = TextMessage(
                text=get_ai_reply(text, session_id=session_id)
            )

        messages = [message]

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages,
            )
        )