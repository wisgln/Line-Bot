"""處理文字訊息，整合 AI、景點字卡與文化功能。"""

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
    QuickReply,
    QuickReplyItem,
    MessageAction,
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
    """泰雅文化主題選單，加上第一題 Quiz。"""
    try:
        from modules.culture.culture_flex import create_culture_menu
        from modules.culture.quiz import create_quiz_flex

        messages = []

        for data, title in (
            (create_culture_menu(), "泰雅文化探索"),
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
        logger.exception("Merchant cards failed")
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
            from modules.merchant.merchant_cards import (
                load_merchants, create_merchant_bubble, flex_message,
            )
            matches = [
                item for item in load_merchants()
                if item.get("name") == stop.get("name")
                and (not stop.get("id") or str(item.get("id")) == str(stop["id"]))
            ]
            if len(matches) == 1:
                return flex_message(
                    f"第{number}站｜{matches[0]['name']}",
                    create_merchant_bubble(matches[0], detailed=True),
                )
            lines = [f"📍 第{number}站｜{stop['name']}"]
            if stop.get("note"):
                lines.append(stop["note"])
            lines.append("🌷 這站沒有對應的店家資料，可依當天安排彈性調整。")
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

        from modules.attraction.flex_message import create_attraction_bubble
        return FlexMessage(alt_text=f"景點介紹｜{matches[0]['name']}"[:100],
                           contents=FlexContainer.from_dict(create_attraction_bubble(matches[0])))

    except Exception:
        logger.exception("Itinerary card failed")
        return TextMessage(
            text="🌿 這站的資料暫時無法顯示，請稍後再試。"
        )


def get_travel_assistant_message():
    """旅遊助手：天氣、交通、緊急聯絡、AI 問答的入口。"""
    items = [
        QuickReplyItem(action=MessageAction(label="🌤 天氣", text="天氣")),
        QuickReplyItem(action=MessageAction(label="🚌 交通", text="交通")),
        QuickReplyItem(
            action=MessageAction(label="🚨 緊急聯絡", text="緊急聯絡")
        ),
        QuickReplyItem(action=MessageAction(label="🤖 AI 問答", text="AI 問答")),
    ]

    return TextMessage(
        text="🧳 旅遊助手\n想查什麼？點下方按鈕，或直接打字問我。",
        quick_reply=QuickReply(items=items),
    )


def get_smart_itinerary_message():
    """智慧行程：選擇半日或一日。"""
    items = [
        QuickReplyItem(
            action=MessageAction(label="☀️ 半日行程", text="幫我排半日行程")
        ),
        QuickReplyItem(
            action=MessageAction(label="🌄 一日行程", text="幫我排一日行程")
        ),
    ]

    return TextMessage(
        text="🗺 智慧行程\n想排多久的行程？也可以直接打字告訴我人數、交通方式或想去的地方。",
        quick_reply=QuickReply(items=items),
    )


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

    elif text == "旅遊助手":
        messages = [get_travel_assistant_message()]

    elif text == "智慧行程":
        messages = [get_smart_itinerary_message()]

    elif text == "AI 問答":
        messages = [
            TextMessage(
                text="🤖 想問什麼都可以直接打字問我喔！\n例如：「小烏來怎麼去」「適合親子的景點」。"
            )
        ]

    else:
        session_id = get_session_id(event)
        message = get_itinerary_message(text, session_id)
        if message is None:
            message = get_merchant_card_message(text)
        if message is None:
            message = get_named_attraction_message(text)
        if message is None:
            message = TextMessage(text=get_ai_reply(text, session_id=session_id))
        messages = [message]

    # 準備好訊息後只送出一次，避免失敗時重複使用 reply token。
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages,
            )
        )