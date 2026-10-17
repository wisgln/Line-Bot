"""處理文字訊息，整合 AI、景點字卡與文化功能。"""

import logging
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
    """延後載入，避免單一模組異常影響整個 Bot。"""
    try:
        from modules.ai_service import get_reply

        return get_reply(text, session_id=session_id)
    except Exception:
        logger.exception("AI reply failed")
        return "🌿 暫時無法回答，請稍後再試一次。"


def get_culture_messages():
    """保留文化介紹與 Quiz 字卡。"""
    try:
        from modules.culture.culture_flex import create_culture_menu
        from modules.culture.quiz import create_quiz_flex

        messages = []

        culture_flex = create_culture_flex("")
        if culture_flex:
            messages.append(
                FlexMessage(
                    alt_text="泰雅文化探索",
                    contents=FlexContainer.from_dict(culture_flex),
                )
            )

        quiz_flex = create_quiz_flex("quiz001")
        if quiz_flex:
            messages.append(
                FlexMessage(
                    alt_text="泰雅文化知識挑戰",
                    contents=FlexContainer.from_dict(quiz_flex),
                )
            )

        return messages
    except Exception:
        logger.exception("Culture cards failed")
        return []


def get_attraction_message():
    """保留原有景點導覽，顯示前 12 張卡片。"""
    try:
        from modules.attraction.attraction_service import (
            get_all_attractions,
        )
        from modules.attraction.flex_message import (
            create_attraction_carousel,
        )

        attractions = get_all_attractions()[:12]
        if not attractions:
            return None

        carousel = create_attraction_carousel(attractions)

        return FlexMessage(
            alt_text="復興區景點導覽",
            contents=FlexContainer.from_dict(carousel),
        )
    except Exception:
        logger.exception("Attraction carousel failed")
        return None


def normalize_card_query(text):
    """統一全半形、空白與標點，供景點名稱比對。"""
    return "".join(
        char
        for char in unicodedata.normalize("NFKC", text).casefold()
        if not char.isspace()
        and not unicodedata.category(char).startswith("P")
    )


def extract_attraction_keyword(text):
    """只接受簡短景點查詢，避免攔截行程或其他完整問題。"""
    query = normalize_card_query(text)

    prefixes = (
        "可以介紹一下",
        "可以介紹",
        "請介紹一下",
        "幫我介紹",
        "我想了解",
        "我想看",
        "介紹一下",
        "請介紹",
        "介紹",
        "查詢",
        "查看",
        "看看",
        "看",
    )

    suffixes = (
        "的詳細介紹",
        "的介紹",
        "的字卡",
        "的卡片",
        "的地圖",
        "的導航",
        "詳細介紹",
        "介紹",
        "字卡",
        "卡片",
        "地圖",
        "導航",
    )

    for prefix in prefixes:
        if query.startswith(prefix):
            query = query[len(prefix):]
            break

    for suffix in suffixes:
        if query.endswith(suffix):
            query = query[:-len(suffix)]
            break

    return query


def get_named_attraction_message(text):
    """明確查詢景點名稱時回傳字卡；其他問題交回 AI 入口。"""
    try:
        from modules.attraction.attraction_service import (
            get_all_attractions,
        )
        from modules.attraction.flex_message import (
            create_attraction_bubble,
        )

        attractions = get_all_attractions()
        if not isinstance(attractions, list):
            return None

        attractions = [
            item
            for item in attractions
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and item["name"].strip()
        ]

        query = normalize_card_query(text)

        # 完整店名先比對，不需要猜測使用者意圖。
        exact_matches = [
            item
            for item in attractions
            if normalize_card_query(item["name"]) == query
        ]

        if exact_matches:
            matches = exact_matches
        else:
            # 景點名稱可能出現在求救、交通或行程問題中。
            # 這些問題應由統一入口處理，不直接回字卡。
            from modules.ai_service.emergency import get_emergency_reply
            from modules.ai_service.gemini_reply import is_planning

            if get_emergency_reply(text) is not None:
                return None

            if is_planning(text):
                return None

            keyword = extract_attraction_keyword(text)

            if len(keyword) < 2:
                return None

            # 移除「介紹」「地圖」等外層用語後，
            # 剩餘文字必須能直接對應景點名稱。
            matches = [
                item
                for item in attractions
                if normalize_card_query(item["name"]) == keyword
            ]

            if not matches:
                matches = [
                    item
                    for item in attractions
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

        attraction = matches[0]
        bubble = create_attraction_bubble(attraction)

        return FlexMessage(
            alt_text=f"景點介紹｜{attraction['name']}"[:100],
            contents=FlexContainer.from_dict(bubble),
        )

    except Exception:
        logger.exception("Named attraction card failed")
        return None


def get_session_id(event):
    """區分私人、群組、聊天室及使用者。"""
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
    messages = []

    if text == "postback":
        buttons_template = ButtonsTemplate(
            title="Postback Sample",
            text="Postback Actions",
            actions=[
                PostbackAction(
                    label="Postback Action",
                    text="Postback Action Button Clicked!",
                    data="postback",
                )
            ],
        )

        messages = [
            TemplateMessage(
                alt_text="Postback Sample",
                template=buttons_template,
            )
        ]

    elif text == "附近景點推薦":
        messages = [
            TextMessage(
                text="📍 請傳送你的目前位置，我幫你找附近景點！"
            )
        ]

    elif text == "景點導覽":
        attraction_message = get_attraction_message()

        messages = [
            attraction_message
            if attraction_message is not None
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
        attraction_message = get_named_attraction_message(text)

        if attraction_message is not None:
            messages = [attraction_message]
        else:
            reply_text = get_ai_reply(
                text,
                session_id=get_session_id(event),
            )
            messages = [TextMessage(text=reply_text)]

    # 準備好訊息後只送出一次，避免失敗時重複使用 reply token。
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages,
            )
        )