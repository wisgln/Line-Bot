"""生活資訊 Flex 字卡；沿用本地資料與天氣服務，不呼叫生成式 AI。"""
import logging
import re

from linebot.v3.messaging import TextMessage
from modules.merchant.merchant_cards import (
    flex_message, text_item, message_button, uri_button,
)
from .intent import normalize, detect_intent
from .emergency import is_emergency_query, load_emergency_contacts, FALLBACK_REPLY
from .local_products import load_products, GENERAL_WORDS, PRODUCT_WORDS

logger = logging.getLogger(__name__)
PAGE_SIZE = 6
CWA_URL = "https://www.cwa.gov.tw/"


def bubble(title, subtitle, contents, buttons=(), color="#237A65"):
    result = {
        "type": "bubble", "size": "mega",
        "header": {"type": "box", "layout": "vertical", "spacing": "sm",
                   "backgroundColor": color, "contents": [
                       text_item(title, size="xl", bold=True, color="#FFFFFF"),
                       text_item(subtitle, size="xs", color="#FFFFFF"),
                   ]},
        "body": {"type": "box", "layout": "vertical", "spacing": "md",
                 "contents": contents},
    }
    if buttons:
        result["footer"] = {"type": "box", "layout": "vertical", "spacing": "sm",
                            "contents": [item for item in buttons if item is not None]}
    return result


def get_emergency_card(text):
    if not is_emergency_query(text):
        return None
    try:
        contacts = load_emergency_contacts()
        contents = [text_item("有立即危險，請直接撥打適當專線。", bold=True)]
        buttons = []
        for contact in contacts:
            contents.extend([
                text_item(contact["phone"] + "｜" + contact["name"], bold=True),
                text_item(contact["description"], size="xs"),
            ])
            # 電話已經由資料載入器驗證，只建立撥號入口，不自動撥號。
            buttons.append({"type": "button", "style": "primary", "color": "#B42318",
                            "height": "sm", "action": {"type": "uri",
                            "label": contact["phone"] + " " + contact["name"],
                            "uri": "tel:" + contact["phone"]}})
        contents.extend([
            text_item("📍 請說明所在位置、附近地標與現場狀況。", size="sm"),
            text_item("本系統不會代為報案，也未通知救援單位。", bold=True, size="xs"),
            text_item("手機點按下方按鈕開啟撥號；若裝置不支援，請手動撥號。", size="xs"),
        ])
        return flex_message("緊急聯絡｜119／110／165｜本系統未代為報案", bubble(
            "☎ 緊急聯絡", "台灣適用・重要電話集中查看", contents, buttons, "#B42318"))
    except Exception:
        logger.exception("Emergency card failed")
        return TextMessage(text=FALLBACK_REPLY)


def get_weather_card():
    from modules.weather.weather_service import get_weather_reply
    try:
        answer = get_weather_reply()
        if not answer.startswith("桃園市復興區｜近期天氣預報"):
            raise ValueError("Weather service did not return a forecast")
        # 使用服務已配對好的時段與官方綜合描述，不猜測數值或拼接時段。
        lines = [line.strip() for line in answer.splitlines() if line.strip()]
        periods = []
        for index, line in enumerate(lines):
            if re.fullmatch(r"\d{2}/\d{2} \d{2}:\d{2}～\d{2}/\d{2} \d{2}:\d{2}", line):
                periods.append((line, lines[index + 1]))
        if not periods:
            raise ValueError("No valid forecast periods")
        checked = next(line for line in lines if line.startswith("查詢時間："))
        cards = [bubble("🌤 復興區天氣", period, [
            text_item(description), text_item(checked, size="xs"),
            text_item("中央氣象署預報，非即時觀測；請依實際天候調整行程。", size="xs"),
        ], [message_button("↻ 更新天氣", "復興區天氣"), uri_button("中央氣象署", CWA_URL)],
            color="#246B9E") for period, description in periods[:3]]
        return flex_message("復興區近期天氣｜左右滑動查看預報時段", {"type": "carousel", "contents": cards})
    except Exception:
        logger.warning("Weather forecast unavailable for card")
        return flex_message("天氣暫時無法取得", bubble("🌦 天氣查詢", "桃園市復興區", [
            text_item("暫時無法取得最新預報，請稍後重試，或開啟中央氣象署查詢。"),
        ], [message_button("重新查詢", "復興區天氣"), uri_button("中央氣象署", CWA_URL)], "#246B9E"))


def product_bubble(item):
    return bubble("🌿 " + item["name"], item["group"], [
        text_item("✨ 特色", bold=True), text_item(item["description"]),
        text_item("🗓 產季參考", bold=True), text_item(item["season"]),
        text_item("採收受品種、海拔與天候影響；產季不代表目前有現貨。", size="xs"),
        text_item("先向農會確認品項、價格與取貨方式，再安排購買。", size="xs"),
        text_item("資料查詢：" + item["checked_on"], size="xs"),
    ], [uri_button("🛍 農會購買資訊", item["purchase_url"]),
        uri_button("📖 產季資料來源", item["source_url"]),
        message_button("看其他農特產", "農特產")])


def get_product_card(text):
    query = normalize(text)
    page_match = re.fullmatch(r"農產列表第([0-9]{1,4})頁", query)
    detail = re.fullmatch(r"農產介紹(.+)", query)
    if not (page_match or detail or any(word in query for word in GENERAL_WORDS + PRODUCT_WORDS)):
        return None
    try:
        entries = load_products()
        matches = [item for item in entries if any(normalize(word) in query for word in item["keywords"])]
        if detail:
            matches = [item for item in entries if normalize(item["name"]) == detail.group(1)]
            if not matches:
                return TextMessage(text="這項農產資料已更新，請輸入「農特產」重新選擇。")
        if len(matches) > 1 and any(word in query for word in ("加工", "米乖乖", "霜淇淋", "甘糀")):
            processed = [item for item in matches if item["name"] == "水蜜桃加工伴手禮"]
            if processed and not any(word in query for word in ("和", "與", "還有")):
                matches = processed
        if len(matches) == 1 and not page_match:
            return flex_message("農特產介紹｜" + matches[0]["name"], product_bubble(matches[0]))
        selection = entries if page_match else (matches or entries)
        page = int(page_match.group(1)) if page_match else 1
        pages = (len(selection) + PAGE_SIZE - 1) // PAGE_SIZE
        if not 1 <= page <= pages:
            return TextMessage(text="這一頁不存在，請輸入「農特產」重新選擇。")
        selected = selection[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
        buttons = [message_button(item["name"][:20], "農產介紹：" + item["name"]) for item in selected]
        # 翻頁僅用在完整清單，避免下一頁遺失原篩選條件。
        if selection == entries:
            if page > 1:
                buttons.append(message_button("← 上一頁", f"農產列表：第{page-1}頁"))
            if page < pages:
                buttons.append(message_button("下一頁 →", f"農產列表：第{page+1}頁"))
        note = "點選品名，看特色、產季與農會洽詢入口。"
        if any(word in query for word in ("附近", "最近", "周邊", "週邊")):
            note += "此清單未依位置排序，不代表最近的販售地點。"
        return flex_message("復興農特產｜選擇品名", bubble("🌿 山裡好物", f"第 {page}／{pages} 頁", [text_item(note)] + buttons))
    except Exception:
        logger.exception("Product cards failed")
        return TextMessage(text="農產資料暫時讀取不順，請稍後再試。")


def get_info_card(text, session_id=None):
    """普通生活查詢走字卡；行程修改仍交回原本規劃入口。"""
    if not isinstance(text, str) or not text.strip() or len(text) > 2000:
        return None
    emergency = get_emergency_card(text)
    if emergency is not None:
        return emergency
    from .gemini_reply import is_planning, has_session
    from .ai_service import PLAN_EDIT_WORDS
    query = normalize(text)
    if is_planning(text) or (has_session(session_id) and any(word in query for word in PLAN_EDIT_WORDS)):
        return None
    intent = detect_intent(text)
    if intent == "weather":
        return get_weather_card()
    if intent in {"traffic", "merchant", "lodging", "nearby_merchant"}:
        return None
    # 商家名稱可能含「咖啡」「水蜜桃」，保留既有商家字卡入口。
    from modules.merchant.merchant_cards import load_merchants, merchant_keyword
    try:
        keyword = merchant_keyword(text)
        if any(normalize(item["name"]) == keyword for item in load_merchants()):
            return None
    except (OSError, ValueError):
        logger.warning("Merchant lookup unavailable during info routing")
    return get_product_card(text)
