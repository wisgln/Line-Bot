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
                "復興區｜道路與開車資訊",
                "",
                "出發前，請透過下方公路局連結"
                "查看沿途最新路況與管制公告。",
                "",
                "停車位請以停車場現場資訊為準；"
                "實際通行請依現場指示及主管機關公告。",
                "",
                "公路局省道即時資訊：",
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

    lines = ["復興區｜交通參考", NOTICE]

    if not matches:
        lines.extend(
            [
                "",
                "目前收錄角板山、小烏來與拉拉山的交通參考。",
                "可輸入「怎麼去角板山」「小烏來公車」"
                "或「拉拉山交通」。",
                "其他目的地目前未提供專屬路線，"
                "請至官方網站查詢。",
            ]
        )
    elif len(matches) > 1:
        lines.extend(
            [
                "",
                "以下分別列出各地交通參考，"
                "不是這些地點之間的轉乘規劃；"
                "轉乘方式請依實際起訖站與班次確認。",
            ]
        )

    for entry in matches:
        lines.append(f"\n【{entry['name']}】")
        lines.extend(f"・{note}" for note in entry["notes"])
        lines.append(
            f"官方路線／交通說明：\n{entry['source_url']}"
        )
        lines.append(f"資料查閱日期：{entry['checked_on']}")

    lines.extend(
        [
            "",
            "查詢班次與公車動態：",
            BUS_URL,
            "",
            "查詢省道路況：",
            ROAD_URL,
            "",
            "實際行駛、票價及管制資訊"
            "以主管機關與業者公告為準。",
        ]
    )

    return "\n".join(lines)


if __name__ == "__main__":
    print(get_traffic_reply("怎麼去角板山"))