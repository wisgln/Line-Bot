"""在送入 Gemini 前篩選、縮減公開旅遊參考資料。"""

import json
import re
import unicodedata


MAX_CONTEXT_CHARS = 10000
MAX_CANDIDATES = 8


class ContextBudgetError(ValueError):
    pass


def json_text(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def normalize(value):
    return "".join(
        char
        for char in unicodedata.normalize("NFKC", str(value)).casefold()
        if not char.isspace()
        and not unicodedata.category(char).startswith("P")
    )


def short(value, limit):
    value = str(value).strip()
    if len(value) <= limit:
        return value
    return value[:limit] + "…"


def history_questions(history):
    questions = []

    for message in history[-8:]:
        if message.get("role") != "user":
            continue
        for part in message.get("parts", []):
            if isinstance(part.get("text"), str):
                questions.append(part["text"])

    return " ".join(questions)


def rows(value):
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        for key in ("items", "products", "local_products", "faq"):
            if isinstance(value.get(key), list):
                return rows(value[key])

    return []


def select(entries, query, *, pinned_ids=(), pinned_names=(), limit=8):
    """明確名稱、既有行程優先，其餘用文字重疊排序。"""
    pinned_ids = {str(value) for value in pinned_ids}
    pinned_names = {normalize(value) for value in pinned_names}
    query = normalize(query)

    def required(item):
        name = normalize(item.get("name", ""))
        return (
            str(item.get("id")) in pinned_ids
            or name in pinned_names
            or (len(name) >= 2 and name in query)
        )

    def score(item):
        searchable = normalize(
            " ".join(
                str(item.get(key, ""))
                for key in (
                    "name", "category", "address",
                    "description", "tags", "question", "keywords",
                )
            )
        )
        # 簡單文字比對，不是距離、交通或設施適合度評分。
        grams = {
            query[index:index + 2]
            for index in range(max(0, len(query) - 1))
        }
        return sum(part in searchable for part in grams)

    pinned = [item for item in entries if required(item)]
    others = [item for item in entries if not required(item)]
    others.sort(key=score, reverse=True)

    selected = pinned + others[:max(0, limit - len(pinned))]
    return selected, {id(item) for item in pinned}


def pick(item, fields):
    return {
        key: item[key]
        for key in fields
        if key in item and item[key] not in ("", None, [], {})
    }


def attraction_summary(item, include_links):
    result = pick(
        item,
        (
            "id", "name", "category", "address",
            "opening_hours", "source_checked_on",
        ),
    )

    for key, limit in (
        ("description", 130),
        ("accessibility", 100),
        ("parking", 100),
        ("walking_notes", 100),
        ("suggested_duration", 60),
    ):
        if item.get(key) not in ("", None, [], {}):
            result[key] = short(item[key], limit)

    if isinstance(item.get("tags"), list):
        result["tags"] = item["tags"][:5]

    result["hours_verified"] = bool(
        item.get("source_url") and item.get("source_checked_on")
    )

    if include_links:
        result.update(pick(item, ("maps_url", "source_url")))

    return result


def merchant_summary(item, include_links):
    result = pick(
        item,
        (
            "id", "name", "category", "address",
            "currency", "source_checked_on", "information_checked_on",
        ),
    )

    if item.get("description"):
        result["description"] = short(item["description"], 110)

    # 不把單點、套餐、不同房型混成不可靠的最低～最高價格。
    prices = [
        pick(price, ("name", "price", "unit"))
        for price in item.get("price_items", [])
        if isinstance(price, dict)
    ][:2]

    if prices:
        result["price_items"] = prices

    result["price_status"] = "歷史參考；不代表總花費或即時售價"

    if item.get("price_note"):
        result["price_note"] = short(item["price_note"], 140)

    if include_links:
        result.update(
            pick(
                item,
                (
                    "maps_url", "source_url", "information_source_url",
                    "website", "official_url", "booking_url",
                ),
            )
        )

    return result


def supplementary_summary(item, include_links):
    """農產與 FAQ 保留基本文字，避免整份資料直接送出。"""
    result = {}

    limits = {
        "id": 60,
        "name": 100,
        "category": 60,
        "question": 150,
        "answer": 450,
        "description": 250,
        "season": 100,
        "season_note": 160,
        "price_note": 140,
        "source_checked_on": 30,
        "checked_on": 30,
    }

    for key, limit in limits.items():
        if item.get(key) not in ("", None, [], {}):
            result[key] = short(item[key], limit)

    for key in ("tags", "keywords", "months", "season_months"):
        if isinstance(item.get(key), list):
            result[key] = item[key][:12]

    if include_links:
        result.update(pick(item, ("source_url", "maps_url")))

    return result


def compact_context(raw, text, history=()):
    current = normalize(text)
    combined = normalize(text + " " + history_questions(history))
    plan = raw.get("current_plan") or []

    if not isinstance(plan, list):
        raise ValueError("Invalid current plan")

    pinned_ids = [
        stop["id"]
        for stop in plan
        if stop.get("kind") == "attraction" and "id" in stop
    ]
    pinned_names = [
        stop["name"]
        for stop in plan
        if stop.get("kind") == "other" and stop.get("name")
    ]

    include_links = any(
        word in current
        for word in ("網址", "連結", "地圖", "導航", "官網", "訂房", "報名", "來源")
    )
    planning = bool(plan) or any(
        word in combined
        for word in ("行程", "規劃", "一日遊", "半日遊", "兩天", "二天", "三天")
    )

    result = {
        "notice": (
            "這是篩選後的候選資料，不代表完整清單或最適合選項。"
            "缺少欄位表示未知。介紹可能節錄。"
            "開放時間、價格、設施不是即時驗證結果。"
        ),
        "current_plan": plan,
    }

    # groups 用於預算超標時先移除非必要候選。
    groups = []

    attraction_data = raw.get("attractions", {})
    attraction_rows = rows(attraction_data)
    named_attraction = any(
        len(normalize(item.get("name", ""))) >= 2
        and normalize(item.get("name", "")) in current
        for item in attraction_rows
    )
    need_attractions = planning or named_attraction or any(
        word in current for word in ("景點", "走走", "哪裡玩")
    )

    result["attractions"] = {
        "status": attraction_data.get("status", "missing"),
        "items": [],
    }

    if need_attractions:
        chosen, pinned = select(
            attraction_rows,
            text + " " + history_questions(history),
            pinned_ids=pinned_ids,
            limit=MAX_CANDIDATES,
        )
        packed = [
            (attraction_summary(item, include_links), id(item) in pinned)
            for item in chosen
        ]
        result["attractions"]["items"] = [item for item, _ in packed]
        groups.append((result["attractions"]["items"], packed))

    merchants = rows(raw.get("merchants.json", []))
    need_food = planning or any(
        word in current for word in ("餐廳", "吃", "午餐", "晚餐", "美食")
    )
    need_lodging = any(
        word in combined
        for word in ("住宿", "民宿", "過夜", "訂房", "兩天", "二天", "三天")
    )

    candidates = []
    for item in merchants:
        name = normalize(item.get("name", ""))
        category = str(item.get("category", ""))
        explicit = (
            name in {normalize(value) for value in pinned_names}
            or (len(name) >= 2 and name in current)
        )
        if (
            explicit
            or (need_food and category == "餐廳")
            or (need_lodging and category == "民宿")
        ):
            candidates.append(item)

    # 餐廳、住宿各自最多8筆，避免同一分類占滿全部候選。
    result["merchants.json"] = []
    merchant_packed = []

    for category in sorted({str(item.get("category", "")) for item in candidates}):
        chosen, pinned = select(
            [item for item in candidates if str(item.get("category", "")) == category],
            text + " " + history_questions(history),
            pinned_names=pinned_names,
            limit=MAX_CANDIDATES,
        )
        merchant_packed.extend(
            (merchant_summary(item, include_links), id(item) in pinned)
            for item in chosen
        )

    result["merchants.json"] = [item for item, _ in merchant_packed]
    groups.append((result["merchants.json"], merchant_packed))

    for key, keywords in (
        ("local_products.json", ("農特產", "農產", "伴手禮", "當季", "產季", "水蜜桃", "甜柿")),
        ("faq.json", ("系統", "使用說明", "怎麼用", "下載", "分享位置", "功能")),
    ):
        entries = rows(raw.get(key, []))
        explicit = any(
            len(normalize(item.get("name", ""))) >= 2
            and normalize(item.get("name", "")) in current
            for item in entries
        )
        if explicit or any(word in current for word in keywords):
            chosen, _ = select(entries, text, limit=5)
            packed = [
                (supplementary_summary(item, include_links), False)
                for item in chosen
            ]
            result[key] = [item for item, _ in packed]
            groups.append((result[key], packed))

    if any(word in current for word in ("活動", "市集", "祭典", "慶典")):
        event_data = raw.get("events", {})
        result["events"] = {
            "status": event_data.get("status", "unavailable"),
            "as_of": event_data.get("as_of"),
            "notice": "公告期間不代表每日有場次；報名與異動需確認。",
            "items": [],
        }
        packed = []
        for event in rows(event_data)[:3]:
            item = pick(
                event,
                ("id", "name", "start_date", "end_date", "location", "checked_on"),
            )
            item["schedule_note"] = short(event.get("schedule_note", ""), 160)
            if include_links:
                item.update(pick(event, ("source_url",)))
            packed.append((item, False))
        result["events"]["items"] = [item for item, _ in packed]
        groups.append((result["events"]["items"], packed))
    else:
        result["events"] = {
            "status": "not_selected",
            "items": [],
            "notice": "本次未提供活動資料，不可沿用歷史活動推薦。",
        }

    # 輪流移除各類排名較後、且非使用者指定的候選。
    while len(json_text(result)) > MAX_CONTEXT_CHARS:
        removed = False

        for target, packed in sorted(groups, key=lambda group: len(group[0]), reverse=True):
            for index in range(len(packed) - 1, -1, -1):
                item, required = packed[index]
                if not required:
                    packed.pop(index)
                    target[:] = [entry for entry, _ in packed]
                    removed = True
                    break
            if removed:
                break

        if not removed:
            raise ContextBudgetError(
                "Required itinerary data exceeds context budget"
            )

    result["attractions"]["selected_count"] = len(
        result["attractions"]["items"]
    )
    result["attractions"]["total_count"] = len(attraction_rows)

    # 計數欄位也算入最終限制。
    if len(json_text(result)) > MAX_CONTEXT_CHARS:
        result["attractions"].pop("selected_count", None)
        result["attractions"].pop("total_count", None)

    return result


if __name__ == "__main__":
    from .openai_reply import build_context
    from .attraction_context import load_attraction_context
    from .events import event_context

    raw = build_context()
    raw["attractions"] = load_attraction_context()
    raw["events"] = event_context()
    raw["current_plan"] = []

    question = "從桃園開車，兩位大人，安排復興兩天一夜，推薦餐廳民宿"
    compact = compact_context(raw, question)

    print("原始參考資料字數：", len(json_text(raw)))
    print("精簡參考資料字數：", len(json_text(compact)))
    print("景點候選數：", len(compact["attractions"]["items"]))
    print("商家候選數：", len(compact["merchants.json"]))
    print("含FAQ：", "faq.json" in compact)
    print("含農特產：", "local_products.json" in compact)