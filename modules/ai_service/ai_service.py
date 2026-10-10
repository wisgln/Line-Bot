"""提供 FAQ、天氣、商家、緊急聯絡與交通資訊的統一入口。"""

import logging

from .emergency import get_emergency_reply
from .faq import find_answer, load_faq
from .intent import detect_intent, normalize
from .traffic import get_traffic_reply

logger = logging.getLogger(__name__)

WELCOME = (
    "你好！目前提供系統使用 FAQ、復興區天氣預報、"
    "商家查詢、緊急聯絡與交通資訊。"
    "可以問我：需要下載 App 嗎？"
    "復興區天氣如何？肚子餓了，有什麼能吃？"
    "拉拉山要搭什麼車？"
    "也可以輸入店家名稱或「緊急聯絡」。"
)

FALLBACK = (
    "目前找不到對應的答案。請一次問一個問題，"
    "或輸入「使用說明」查看可用內容。"
)

NEARBY_REPLY = (
    "附近推薦需要你的位置，並由定位模組計算距離。"
    "這項功能待整合後提供；目前可先輸入"
    "「推薦餐廳」或「民宿」查看已收錄資料。"
    "這些清單不代表距離你最近的商家。"
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
        "FAQ 模組尚未接入景點資料；"
        "景點導覽與附近推薦需由對應模組整合後提供。"
    ),
    "culture": (
        "FAQ 模組尚未接入文化資料；"
        "泰雅文化內容需由文化模組整合後提供。"
    ),
}


def get_reply(text: str, *, faq_path=None) -> str:
    """回傳文字，由呼叫端負責傳送至 LINE。"""
    query = normalize(text)

    if len(text) > 2000:
        return "問題太長了，請縮短至 2000 字以內，並一次問一個問題。"

    if not query or query in {
        "ai問答",
        "menuai",
        "使用說明",
        "help",
        "你好",
        "開始",
    }:
        return WELCOME

    # 緊急聯絡優先於其他查詢。
    emergency_reply = get_emergency_reply(text)
    if emergency_reply is not None:
        return emergency_reply

    intent = detect_intent(text)

    traffic_reply = get_traffic_reply(text)
    if traffic_reply is not None:
        return traffic_reply

    # 新交通問法保留原問題中的地名。
    if intent == "traffic":
        return get_traffic_reply(f"交通 {text}")

    try:
        answer = find_answer(text, load_faq(faq_path))
    except (OSError, ValueError):
        logger.exception("Unable to load FAQ data")
        return "FAQ 資料暫時無法讀取，請稍後再試，或通知專題管理者。"

    if answer is not None:
        return answer

    if intent == "weather":
        from modules.weather.weather_service import get_weather_reply

        return get_weather_reply()

    # 尚未整合定位，不把全部商家當成附近推薦。
    if intent == "nearby_merchant":
        return NEARBY_REPLY

    # 避免用商家介紹冒充優惠券資訊。
    if "優惠券" in query:
        return PENDING["merchant"]

    from modules.merchant.merchant_service import (
        get_merchant_reply,
        load_merchants,
    )

    try:
        merchants = load_merchants()
    except (OSError, ValueError):
        logger.exception("Unable to load merchant data")
        merchants = []

    # 店名優先，避免「泰雅」等字詞被當成文化問題。
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

    # 保留原本的明確分類查詢。
    if any(word in query for word in ("餐廳", "美食")):
        return get_merchant_reply("餐廳")

    if any(word in query for word in ("民宿", "住宿")):
        return get_merchant_reply("民宿")

    if "商家" in query:
        return get_merchant_reply("商家")

    # 自然問法轉成商家模組支援的分類。
    if intent == "lodging":
        return get_merchant_reply("民宿")

    if intent == "merchant":
        return get_merchant_reply("餐廳")

    return PENDING.get(intent, FALLBACK)