"""提供台灣緊急聯絡資訊，不代替使用者報案。"""

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

from .intent import normalize

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "emergency.json"

# 固定專線也用來驗證資料，避免誤植電話。
EXPECTED_PHONES = {
    "fire_rescue": "119",
    "police": "110",
    "anti_fraud": "165",
}

EMERGENCY_KEYWORDS = (
    "緊急",
    "求救",
    "救命",
    "救護車",
    "叫救護",
    "火災",
    "失火",
    "救援",
    "報警",
    "報案",
    "警察電話",
    "消防電話",
    "詐騙",
    "被騙",
    "受傷",
    "昏倒",
    "昏迷",
    "無法呼吸",
    "呼吸困難",
    "山上迷路",
    "山區迷路",
    "登山迷路",
    "被困",
    "溺水",
)

FALLBACK_REPLY = (
    "緊急联絡資料暫時無法完整讀取。\n"
    "消防、救護與救援：119\n"
    "警察報案：110\n"
    "反詐騙諮詢：165\n\n"
    "本系統不會代為報案，也未通知救援單位。"
    "如有立即危險，請直接撥打適當專線。"
).replace("联", "聯")


def is_emergency_query(text):
    """第一版以明確關鍵字判斷，並非完整的緊急狀況辨識。"""
    query = normalize(text)

    if query in {"119", "110", "165", "sos"}:
        return True

    return any(word in query for word in EMERGENCY_KEYWORDS)


def load_emergency_contacts(data_path=None):
    path = Path(data_path) if data_path is not None else DATA_PATH

    with path.open("r", encoding="utf-8-sig") as file:
        contacts = json.load(file)

    if not isinstance(contacts, list):
        raise ValueError("緊急聯絡資料必須為陣列")

    seen_ids = set()

    for contact in contacts:
        if not isinstance(contact, dict):
            raise ValueError("每筆緊急聯絡資料必須為物件")

        for field in (
            "id",
            "name",
            "phone",
            "description",
            "source_url",
            "checked_on",
        ):
            value = contact.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"缺少有效欄位：{field}")

        contact_id = contact["id"]

        if contact_id in seen_ids:
            raise ValueError("緊急聯絡 id 不可重複")

        if contact_id not in EXPECTED_PHONES:
            raise ValueError("未知的緊急聯絡種類")

        if contact["phone"] != EXPECTED_PHONES[contact_id]:
            raise ValueError("緊急聯絡電話與預期不符")

        source = urlparse(contact["source_url"])
        hostname = source.hostname or ""

        if (
            source.scheme != "https"
            or not hostname.endswith(".gov.tw")
        ):
            raise ValueError("來源必須為 HTTPS 政府網站")

        seen_ids.add(contact_id)

    if seen_ids != set(EXPECTED_PHONES):
        raise ValueError("缺少必要的緊急聯絡資料")

    return contacts


def get_emergency_reply(text, *, data_path=None):
    """符合緊急查詢時回傳文字；其他問題回傳 None。"""
    if not is_emergency_query(text):
        return None

    try:
        contacts = load_emergency_contacts(data_path)
    except (OSError, ValueError):
        logger.exception("Unable to load emergency contacts")
        return FALLBACK_REPLY

    lines = [
        "台灣緊急聯絡資訊（復興區適用）",
        "如有立即危險，請直接撥打適當專線。",
    ]

    for contact in contacts:
        lines.extend(
            [
                f"\n{contact['phone']}｜{contact['name']}",
                contact["description"],
            ]
        )

    lines.extend(
        [
            "\n報案時請說明所在位置、附近地標與現場狀況。",
            "本系統不會代為報案，也未通知救援單位。",
            "\n官方資料來源：",
        ]
    )

    for url in dict.fromkeys(
        contact["source_url"] for contact in contacts
    ):
        lines.append(url)

    return "\n".join(lines)


if __name__ == "__main__":
    print(get_emergency_reply("緊急聯絡"))