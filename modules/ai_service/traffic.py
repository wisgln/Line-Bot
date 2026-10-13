"""提供復興區交通參考與官方查詢連結，不查詢即時交通。"""

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

from .intent import normalize

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "traffic.json"

BUS_URL = "https://ebus.tycg.gov.tw/ebus"
ROAD_URL = "https://168.thb.gov.tw/thb168"

TRAFFIC_KEYWORDS = (
    "交通",
    "公車",
    "客運",
    "班次",
    "時刻表",
    "末班車",
    "首班車",
    "到站",
    "路況",
    "道路管制",
    "封路",
    "通車",
    "怎麼去",
    "怎麼到",
    "怎麼走",
    "如何前往",
    "如何到",
    "怎麼搭",
    "搭車",
    "搭乘",
    "開車",
    "停車",
)

ROAD_KEYWORDS = (
    "路況",
    "道路管制",
    "封路",
    "通車",
    "開車",
    "停車",
)

ALLOWED_SOURCE_HOSTS = {
    "www.taiwantrip.com.tw",
    "recreation.forest.gov.tw",
}

NOTICE = (
    "以下提供交通方式與官方查詢入口。"
    "最新班次、到站時間、票價及道路狀況，"
    "請點選下方官方連結查看。"
)


def is_traffic_query(text):
    """辨識包含明確交通關鍵字的問題。"""
    query = normalize(text)
    return any(word in query for word in TRAFFIC_KEYWORDS)


def load_traffic(data_path=None):
    """讀取並檢查本機交通資料。"""
    path = Path(data_path) if data_path is not None else DATA_PATH

    with path.open("r", encoding="utf-8-sig") as file:
        entries = json.load(file)

    if not isinstance(entries, list) or not entries:
        raise ValueError("交通資料必須為非空陣列")

    seen_ids = set()

    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("每筆交通資料必須為物件")

        for field in ("id", "name", "source_url", "checked_on"):
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"缺少有效欄位：{field}")

        if entry["id"] in seen_ids:
            raise ValueError("交通資料 id 不可重複")
        seen_ids.add(entry["id"])

        for field in ("aliases", "notes"):
            value = entry.get(field)
            if (
                not isinstance(value, list)
                or not value
                or not all(
                    isinstance(item, str) and item.strip()
                    for item in value
                )
            ):
                raise ValueError(f"{field} 必須為非空文字陣列")

        if any(not normalize(alias) for alias in entry["aliases"]):
            raise ValueError("地名別稱不可只有標點或空白")

        source = urlparse(entry["source_url"])
        if (
            source.scheme != "https"
            or source.hostname not in ALLOWED_SOURCE_HOSTS
        ):
            raise ValueError("交通來源網址不在允許的官方網站清單")

    return entries


def get_traffic_reply(text, *, data_path=None):
    """交通問題回傳文字；其他問題回傳 None。"""
    query = normalize(text)

    if not is_traffic_query(text):
        return None

    # 道路相關問題直接提供路況入口，不使用公車資料回答。
    if any(word in query for word in ROAD_KEYWORDS):
        return "\n".join(
            [
                "🚗 復興開車小幫手",
                "",
                "出發前先查沿途路況與管制公告 👇",
                "",
                "🅿️ 停車空位以現場為準。",
                "⚠️ 是否可通行，請依最新公告與現場指示。",
                "",
                "🔎 公路局路況查詢",
                ROAD_URL,
            ]
        )

    try:
        entries = load_traffic(data_path)
    except (OSError, ValueError):
        logger.exception("Unable to load traffic data")
        return "\n".join(
            [
                "交通資料暫時無法讀取，請改用官方網站查詢。",
                "",
                "桃園公車動態資訊：",
                BUS_URL,
                "",
                "公路局省道即時資訊：",
                ROAD_URL,
            ]
        )

    matches = [
        entry
        for entry in entries
        if any(
            normalize(alias) in query
            for alias in entry["aliases"]
        )
    ]

    lines = ["🚌 復興搭車小幫手"]

    if not matches:
        lines.extend(
            [
                "",
                "📍 你想去哪裡？可以直接問：",
                "・怎麼去角板山",
                "・小烏來公車",
                "・拉拉山交通",
                "",
                "其他目的地未提供專屬路線，可在下方公車網站查詢。",
            ]
        )
    elif len(matches) > 1:
        lines.extend(
            [
                "",
                "📍 下面是各目的地的搭車參考，",
                "不是這些地點之間的轉乘規劃。轉乘請再確認起訖站與班次。",
            ]
        )

    for entry in matches:
        lines.append(f"\n📍【{entry['name']}】")
        icons = ("🚏", "📅", "👣", "↩️")
        lines.extend(f"{icons[index] if index < len(icons) else '・'} {note}" for index, note in enumerate(entry["notes"]))
        lines.append(
            f"\n🔗 路線與搭乘說明\n{entry['source_url']}"
        )

    lines.extend(
        [
            "",
            "⏰ 查班次／到站時間",
            BUS_URL,
            "",
            "💡 先查回程，再安心出發！班次與票價以官方最新公告為準。",
        ]
    )

    return "\n".join(lines)


if __name__ == "__main__":
    print(get_traffic_reply("怎麼去角板山"))
