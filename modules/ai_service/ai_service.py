"""Stable entry point for LINE integration; currently rule-based FAQ only."""

import logging

from .faq import find_answer, load_faq
from .intent import detect_intent, normalize

logger = logging.getLogger(__name__)
WELCOME = "你好！目前提供系統使用 FAQ。可以問我：需要下載 App 嗎？如何分享位置？這個系統可以做什麼？"
FALLBACK = "目前找不到對應的 FAQ 答案。請一次問一個問題，或輸入「使用說明」查看可用內容。"
PENDING = {
    "weather": "天氣服務尚未串接，目前無法提供即時天氣或降雨預報。",
    "opening_hours": "目前尚未接入景點營業時間資料，無法確認開放時間；出發前請查閱該景點官方公告。",
    "traffic": "交通服務尚未串接，目前無法確認班次或即時路況；出發前請查閱交通主管機關或業者公告。",
    "merchant": "商家資料尚未接入，目前無法提供經確認的餐廳、民宿或優惠資訊。",
    "attraction": "FAQ 模組尚未接入景點資料；景點導覽與附近推薦需由對應模組整合後提供。",
    "culture": "FAQ 模組尚未接入文化資料；泰雅文化內容需由文化模組整合後提供。",
}


def get_reply(text: str, *, faq_path=None) -> str:
    """Return text only; never call LINE, use reply tokens, or require API keys.

    faq_path is optional for tests/custom data. The default is independent of cwd.
    """
    query = normalize(text)
    if not query or query in {"ai問答", "menu_ai", "使用說明", "help", "你好", "開始"}:
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
    return PENDING.get(detect_intent(text), FALLBACK)
