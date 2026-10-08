"""提供 FAQ 與復興區天氣查詢的統一入口。"""

import logging

from .faq import find_answer, load_faq
from .intent import detect_intent, normalize

logger = logging.getLogger(__name__)

WELCOME = (
    "你好！目前提供系統使用 FAQ 與桃園市復興區天氣預報。"
    "可以問我：需要下載 App 嗎？如何分享位置？復興區天氣如何？"
)

FALLBACK = (
    "目前找不到對應的答案。請一次問一個問題，"
    "或輸入「使用說明」查看可用內容。"
)

PENDING = {
    "opening_hours": "目前尚未接入景點營業時間資料，無法確認開放時間；出發前請查閱該景點官方公告。",
    "traffic": "交通服務尚未串接，目前無法確認班次或即時路況；出發前請查閱交通主管機關或業者公告。",
    "merchant": "商家資料尚未接入，目前無法提供經確認的餐廳、民宿或優惠資訊。",
    "attraction": "FAQ 模組尚未接入景點資料；景點導覽與附近推薦需由對應模組整合後提供。",
    "culture": "FAQ 模組尚未接入文化資料；泰雅文化內容需由文化模組整合後提供。",
}


def get_reply(text: str, *, faq_path=None) -> str:
    """回傳回答文字，由呼叫端負責傳送到 LINE。

    FAQ 不需要 API 授權碼；天氣查詢需要 WEATHER_API_KEY。
    faq_path 可供測試或指定其他 FAQ 資料使用。
    """
    query = normalize(text)

    if not query or query in {
        "ai問答",
        "menu_ai",
        "使用說明",
        "help",
        "你好",
        "開始",
    }:
        return WELCOME

    if len(text) > 2000:
        return "問題太長了，請縮短至 2000 字以內，並一次問一個問題。"

    try:
        answer = find_answer(text, load_faq(faq_path))
    except (OSError, ValueError):
        logger.exception("Unable to load FAQ data")
        return "FAQ 資料暫時無法讀取，請稍後再試，或通知專題管理者。"

    if answer is not None:
        return answer

    intent = detect_intent(text)

    if intent == "weather":
        # 只有查詢天氣時才載入，讓 FAQ 可以獨立使用。
        from modules.weather.weather_service import get_weather_reply

        return get_weather_reply()

    return PENDING.get(intent, FALLBACK)