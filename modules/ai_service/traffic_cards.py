"""依目的地提供交通 Flex 字卡；讀取本地交通資料，不呼叫 AI。"""
import re
import unicodedata
from urllib.parse import urlencode

from linebot.v3.messaging import TextMessage
from modules.merchant.merchant_cards import flex_message, text_item, message_button, uri_button
from .traffic import load_traffic, is_traffic_query, BUS_URL, ROAD_URL

DESTINATIONS = {
    "jiaobanshan": "角板山",
    "xiaowulai": "小烏來天空步道",
    "lalashan": "拉拉山國家森林遊樂區",
    "baling": "上巴陵",
}
MODES = {"choose", "bus", "car", "road", "detail"}


def command(destination, mode):
    return f"交通字卡:{destination}:{mode}"


def card(title, subtitle, lines, buttons):
    from .info_cards import bubble
    return flex_message(title, bubble(title, subtitle, [text_item(line) for line in lines], buttons, color="#326C9B"))


def select_destination(mode="choose", mountain=False):
    keys = ("lalashan", "baling") if mountain else tuple(DESTINATIONS)
    return card("🧭 想去哪裡？", "點一下目的地", [
        "拉拉山範圍較大，森林遊樂區與上巴陵的目的地不同。" if mountain else
        "選擇目的地，再查看搭車、開車或路況資訊。其他地點可使用下方地圖查詢。"
    ], [message_button(DESTINATIONS[key], command(key, mode)) for key in keys] +
        ([] if mountain else [uri_button("其他地點｜地圖查詢", "https://www.google.com/maps")]))


def get_traffic_card(text):
    if not isinstance(text, str) or not text.strip() or len(text) > 2000:
        return None
    query = unicodedata.normalize("NFKC", text).strip()
    if query.startswith("交通字卡:"):
        match = re.fullmatch(r"交通字卡:([a-z]+):([a-z]+)", query)
        if not match or match[1] not in DESTINATIONS or match[2] not in MODES:
            return TextMessage(text="交通選單已更新，請輸入「交通」重新選擇。")
        destination, mode = match.groups()
    else:
        if not is_traffic_query(query) and "導航" not in query:
            return None
        # 規劃與修改行程留給原入口；單純交通問題不帶出整份行程。
        from .gemini_reply import is_planning
        if is_planning(query):
            return None
        mode = "road" if any(w in query for w in ("路況", "封路", "管制", "通車")) else (
            "car" if any(w in query for w in ("開車", "停車", "導航")) else (
                "bus" if any(w in query for w in ("公車", "客運", "搭車", "搭乘", "怎麼搭", "班次", "時刻", "末班", "首班", "到站")) else "choose"))
        matches = []
        if "角板山" in query:
            matches.append("jiaobanshan")
        if "小烏來" in query:
            matches.append("xiaowulai")
        if "拉拉山" in query or "上巴陵" in query:
            if "巨木" in query or "森林遊樂區" in query:
                matches.append("lalashan")
            elif "上巴陵" in query:
                matches.append("baling")
            else:
                return select_destination(mode, mountain=True)
        if not matches and query not in ("交通", "公車", "搭車", "開車", "停車", "路況", "導航"):
            return None
        if len(matches) != 1:
            return select_destination(mode)
        destination = matches[0]

    name = DESTINATIONS[destination]
    choices = [message_button("🚌 搭大眾運輸", command(destination, "bus")),
               message_button("🚗 開車導航", command(destination, "car")),
               message_button("🚧 查道路狀況", command(destination, "road"))]
    if mode == "choose":
        return card("🧭 " + name, "選擇交通方式", ["你想搭車還是開車前往？點下方按鈕查看。"], choices)
    if mode == "road":
        return card("🚧 " + name, "出發前看路況", ["山區道路可能因天候或施工調整。", "點下方查最新公告；本字卡不代表道路目前開放。"],
                    [uri_button("公路局｜即時路況", ROAD_URL), message_button("返回交通選單", command(destination, "choose"))])
    if mode == "car":
        url = "https://www.google.com/maps/dir/?" + urlencode({"api": 1, "destination": "桃園市復興區" + name, "travelmode": "driving"})
        return card("🚗 " + name, "開啟地圖規劃路線", ["地圖開啟後，選擇你的出發位置。", "停車位置與園區入口請以現場標示為準；導航目的地不代表車輛可駛入園區。"],
                    [uri_button("📍 Google Maps 導航", url), message_button("🚧 查道路狀況", command(destination, "road")), message_button("返回交通選單", command(destination, "choose"))])
    try:
        item = next((entry for entry in load_traffic() if entry["id"] == destination), None)
    except (OSError, ValueError):
        item = None
    if item is None:
        return card("🚌 " + name, "查詢適合的班次", ["請在桃園公車系統以「上巴陵」查詢停靠站與路線。" if destination == "baling" else "交通資料暫時讀取不順，可先使用官方查詢。", "選擇出發站與日期，先確認去程與回程。"],
                    [uri_button("查路線與班次", BUS_URL), message_button("返回交通選單", command(destination, "choose"))])
    # 原資料的路線限制完整保留；主卡精簡，完整說明放下一層。
    lines = item["notes"] if mode == "detail" else (
        ["參考路線：5090、5091、5301", "路線終點：林班口", "⚠️ 林班口下車後仍需確認至園區的步行或接駁，並非直達巨木步道。"] if destination == "lalashan" else
        ["參考路線：台灣好行 502 小烏來線", "⚠️ 502 為假日行駛；平日請另查可用路線。", "桃園客運桃園總站 → 小烏來天空步道" if destination == "xiaowulai" else "沿線包含角板山，請確認停靠站與搭乘方向。"])
    lines = list(lines) + ["🌷 出發前查好去回程，班次以官方當日公告為準。"]
    buttons = [uri_button("🕒 查班次與到站", BUS_URL), uri_button("📖 官方路線說明", item["source_url"])]
    if mode != "detail":
        buttons.append(message_button("查看搭乘提醒", command(destination, "detail")))
    buttons.append(message_button("返回交通選單", command(destination, "choose")))
    return card("🚌 " + name, "搭車參考｜非即時班表", lines, buttons)
