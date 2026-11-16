"""FAQ、旅遊規劃及復興區生活資訊的統一入口。"""

import logging

from .emergency import get_emergency_reply
from .faq import find_answer, load_faq
from .intent import detect_intent, normalize
from .traffic import get_traffic_reply
from .local_products import get_local_products_reply
from .events import get_events_reply


logger = logging.getLogger(__name__)

WELCOME = (
    "🌿 歡迎使用復興旅遊小幫手！\n\n"
    "🗓 想排行程？可以說：\n"
    "「我們帶爸媽和小孩，從桃園開車，幫我安排一日遊。」\n\n"
    "🔎 也可以查詢：\n"
    "・餐廳、民宿與農特產\n"
    "・復興區天氣、交通與活動\n"
    "・系統使用說明、緊急聯絡\n\n"
    "💬 規劃過程可以繼續說「第二站換掉」或「少走一點路」。\n"
    "輸入「重新開始」可清除這次 AI 對話。"
)

FALLBACK = (
    "🌿 這個問題還沒有找到對應資訊。\n"
    "可以換個說法，或輸入「使用說明」查看可用功能。"
)

NEARBY_REPLY = (
    "📍 想找附近商家，需要位置與商家距離資料。\n"
    "目前可先輸入「餐廳」或「民宿」查看店家資訊；"
    "清單不代表距離你最近的商家。\n"
    "若要找附近景點，可使用選單的「附近景點推薦」。"
)

PENDING = {
    "opening_hours": (
        "目前尚未接入景點營業時間資料，無法確認開放時間；"
        "出發前請查閱該景點官方公告。"
    ),
    "merchant": (
        "目前提供商家資料查詢，尚未提供優惠券服務。"
        "可輸入「餐廳」「民宿」或店家名稱查詢。"
    ),
    "attraction": (
        "📍 景點可以這樣查看：\n"
        "・點選單「景點導覽」，左右滑動看景點卡片\n"
        "・點選單「附近景點推薦」，再傳送你的位置\n"
        "・想排行程，可以直接說「幫我排一日行程」"
    ),
    "culture": (
        "🌿 想認識泰雅文化，可以這樣玩：\n"
        "・點選單「泰雅文化」，看文化介紹並挑戰 Quiz\n"
        "・輸入「復興有什麼農特產？」，認識在地農產\n"
        "・想排行程，可以直接說「幫我排一日行程」"
    ),
}

DIRECT_QUERIES = {
    "餐廳",
    "民宿",
    "住宿",
    "推薦餐廳",
    "推薦民宿",
    "找餐廳",
    "美食",
    "推薦美食",
    "商家",
    "在地商家",
    "農特產",
    "交通",
    "公車班次",
}

PLAN_EDIT_WORDS = (
    "加入",
    "加進",
    "加上",
    "增加",
    "替換",
    "換成",
    "改成",
    "改去",
    "刪掉",
    "移除",
    "取消",
    "保留",
    "第二站",
    "第三站",
    "原本",
    "剛剛",
)


def get_reply(text: str, *, faq_path=None, session_id=None) -> str:
    """回傳文字，由呼叫端負責傳送至 LINE。"""
    query = normalize(text)

    if len(text) > 2000:
        return "問題太長了，請縮短至 2000 字以內，並一次問一個問題。"

    from .gemini_reply import (
        clear_session,
        enabled,
        get_gemini_reply,
        has_session,
        is_planning,
    )

    if query in {"重新開始", "清除對話", "結束規劃"}:
        clear_session(session_id)
        return "🌱 已清除這次對話，可以開始新的旅遊規劃了。"

    if not query or query in {
        "ai問答",
        "menuai",
        "使用說明",
        "help",
        "你好",
        "開始",
    }:
        return WELCOME

    # 緊急需求一律優先，不送進一般行程規劃。
    emergency_reply = get_emergency_reply(text)
    if emergency_reply is not None:
        return emergency_reply

    intent = detect_intent(text)

    planning = is_planning(text)
    active_session = has_session(session_id)
    editing_plan = active_session and any(
        word in query for word in PLAN_EDIT_WORDS
    )
    plan_request = planning or editing_plan

    # 道路安全查詢優先提供官方查詢回覆。
    urgent_road = any(
        word in query
        for word in ("封路", "道路管制", "通車", "路況")
    )

    if urgent_road:
        traffic_reply = get_traffic_reply(text)
        if traffic_reply is not None:
            return traffic_reply
        return get_traffic_reply(f"交通 {text}") or FALLBACK

    # 已在規劃時，區分交通提問與交通方式的補充。
    # 「我們開車，不想走很多路」是補充條件，應交給 AI。
    # 「小烏來怎麼搭車」是交通查詢，應交給交通模組。
    traffic_question = any(
        word in query
        for word in (
            "交通",
            "怎麼搭",
            "怎麼去",
            "怎麼到",
            "怎麼走",
            "如何搭",
            "如何去",
            "如何到",
            "如何前往",
            "班次",
            "時刻表",
            "末班車",
            "首班車",
            "到站",
            "票價",
            "車資",
            "轉乘",
            "哪裡搭",
            "哪裡上車",
            "幾點",
            "多久",
            "停車場",
            "哪裡停車",
            "公車路線",
        )
    ) or query in DIRECT_QUERIES

    # 單純交通查詢優先於 AI 對話，不修改已儲存的行程。
    if not plan_request and (not active_session or traffic_question):
        traffic_reply = get_traffic_reply(text)
        if traffic_reply is not None:
            return traffic_reply

        if intent == "traffic":
            return get_traffic_reply(f"交通 {text}") or FALLBACK

    # 一般活動查詢走資料模組；加入行程則交給規劃處理。
    if not plan_request:
        events_reply = get_events_reply(text)
        if events_reply is not None:
            return events_reply

    # 一般天氣問題使用天氣模組。
    # 「下雨時修改行程」等規劃需求仍可交給 AI。
    if intent == "weather" and not plan_request:
        from modules.weather.weather_service import get_weather_reply

        return get_weather_reply()

    # 優惠券未提供，不讓 AI 或商家清單冒充優惠資訊。
    if "優惠券" in query:
        return PENDING["merchant"]

    if not plan_request:
        from .query_context import local_lookup
        local_answer = local_lookup(text, faq_path)
        if local_answer is not None:
            return local_answer

    # 規劃問題與後續討論優先於餐廳、住宿等單一分類。
    # 明確的獨立查詢已在上方處理。
    if (
        enabled()
        and query not in DIRECT_QUERIES
        and (plan_request or active_session)
    ):
        reply = get_gemini_reply(text, session_id=session_id)
        if reply is not None:
            return reply

    # AI 未啟用或未回覆時，保留原本交通查詢能力。
    traffic_reply = get_traffic_reply(text)
    if traffic_reply is not None:
        return traffic_reply

    if intent == "traffic":
        return get_traffic_reply(f"交通 {text}") or FALLBACK

    try:
        answer = find_answer(text, load_faq(faq_path))
    except (OSError, ValueError):
        logger.exception("Unable to load FAQ data")
        return "FAQ 資料暫時無法讀取，請稍後再試，或通知專題管理者。"

    if answer is not None:
        return answer

    if intent == "nearby_merchant":
        return NEARBY_REPLY

    from modules.merchant.merchant_service import (
        get_merchant_reply,
        load_merchants,
    )

    try:
        merchants = load_merchants()
    except (OSError, ValueError):
        logger.exception("Unable to load merchant data")
        merchants = []

    # 分類詞本身優先，不被含有分類名稱的店名攔截。
    if query in {"民宿", "住宿", "推薦民宿"}:
        return get_merchant_reply("民宿")

    if query in {"餐廳", "推薦餐廳", "找餐廳", "美食", "推薦美食"}:
        return get_merchant_reply("餐廳")

    # 完整店名優先。
    for merchant in merchants:
        if normalize(merchant["name"]) == query:
            return get_merchant_reply(merchant["name"])

    matched_names = []

    for merchant in merchants:
        name = normalize(merchant["name"])
        if name in query or (len(query) >= 2 and query in name):
            matched_names.append(merchant["name"])

    if len(matched_names) == 1:
        return get_merchant_reply(matched_names[0])

    if len(matched_names) > 1:
        lines = ["找到多間符合的商家，請輸入完整店名："]
        lines.extend(f"・{name}" for name in matched_names[:10])
        return "\n".join(lines)

    # 店名查詢後，再處理一般農特產問題。
    product_reply = get_local_products_reply(text)
    if product_reply is not None:
        return product_reply

    if any(word in query for word in ("餐廳", "美食")):
        return get_merchant_reply("餐廳")

    if any(word in query for word in ("民宿", "住宿")):
        return get_merchant_reply("民宿")

    if "商家" in query:
        return get_merchant_reply("商家")

    if intent == "lodging":
        return get_merchant_reply("民宿")

    if intent == "merchant":
        return get_merchant_reply("餐廳")

    if intent in PENDING:
        return PENDING[intent]

    return get_gemini_reply(text, session_id=session_id) or FALLBACK
