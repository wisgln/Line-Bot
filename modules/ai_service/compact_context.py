"""篩選與縮減旅遊資料；明確地區需求先做文字篩選。"""

import json
import re
import unicodedata


MAX_CONTEXT_CHARS = 10000
MAX_CANDIDATES = 8

AREA_NAMES = (
    "角板山",
    "小烏來",
    "拉拉山",
    "羅浮",
    "上巴陵",
    "巴陵",
    "三民",
)


class ContextBudgetError(ValueError):
    pass


def json_text(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def normalize(value):
    return "".join(
        char
        for char in unicodedata.normalize(
            "NFKC", str(value)
        ).casefold()
        if not char.isspace()
        and not unicodedata.category(char).startswith("P")
    )


def short(value, limit):
    value = str(value).strip()
    if len(value) <= limit:
        return value
    return value[:limit] + "…"


def user_texts(history):
    """只讀取使用者文字，不把 AI 回答當成使用者條件。"""
    for message in history:
        if message.get("role") != "user":
            continue

        for part in message.get("parts", []):
            if isinstance(part.get("text"), str):
                yield part["text"]


def history_questions(history):
    return " ".join(user_texts(history[-8:]))


def requested_area(text, history=()):
    """辨認明確範圍；最新明確條件取代舊條件。"""
    area = None

    for question in [*user_texts(history), text]:
        changes = []

        for clause in re.split(
            r"[，。！？；,!?;\n]",
            question,
        ):
            clause = re.sub(r"\s+", "", clause)

            # 否定句不當成新增或取消範圍的要求。
            if re.match(
                r"^(不要|不想|不去|別|不必)",
                clause,
            ):
                continue

            if clause in (
                "不限地區",
                "不限定地區",
                "取消地區限制",
                "整個復興區都可以",
            ):
                changes.append(None)
                continue

            matches = []

            for name in AREA_NAMES:
                pattern = (
                    re.escape(name)
                    + r"(?:周邊|附近|一帶|地區)"
                )

                for match in re.finditer(pattern, clause):
                    prefix = clause[:match.start()]

                    if re.search(
                        r"(?:不要|不想|不去|不在|排除)$",
                        prefix,
                    ):
                        continue

                    # 不把「上巴陵」同時辨認成「巴陵」。
                    if name == "巴陵" and prefix.endswith("上"):
                        continue

                    matches.append((match.start(), name))

            changes.extend(
                name for _, name in sorted(matches)
            )

        unique = list(dict.fromkeys(changes))

        if len(unique) == 1:
            area = unique[0]

        elif len(unique) > 1:
            # 多地區問題不擅自選其中一個。
            # 此情況不套用單一地區硬篩選。
            area = None

    return area


def area_matches(item, area):
    """地區文字比對，不是地理距離或行政邊界判斷。"""
    if not area:
        return True

    for field in (
        "name",
        "address",
        "area",
        "district",
        "region",
    ):
        value = normalize(item.get(field, ""))

        if area == "巴陵":
            value = value.replace("上巴陵", "")

        if normalize(area) in value:
            return True

    # 不用 description 比對：
    # 簡介可能提到交通途經地或另一個景點。
    return False


def area_note(summary, original, area):
    if area:
        matches = area_matches(original, area)
        summary["area_match"] = matches

        if matches:
            summary["selection_note"] = (
                "名稱或地址等地區文字吻合；"
                "不代表距離、順路或步行限制已確認"
            )
        else:
            summary["selection_note"] = (
                "僅為保留既有行程而提供；"
                "未符合地區文字篩選，"
                "不可當作範圍內新推薦"
            )

    return summary


def rows(value):
    if isinstance(value, list):
        return [
            item for item in value
            if isinstance(item, dict)
        ]

    if isinstance(value, dict):
        for key in (
            "items",
            "products",
            "local_products",
            "faq",
        ):
            if isinstance(value.get(key), list):
                return rows(value[key])

    return []


def select(
    entries,
    query,
    *,
    pinned_ids=(),
    pinned_names=(),
    limit=8,
    area=None,
):
    """先限制地區，再保留行程資料及做文字相關度排序。"""
    pinned_ids = {str(value) for value in pinned_ids}
    pinned_names = {
        normalize(value) for value in pinned_names
    }
    query = normalize(query)

    if area:
        entries = [
            item for item in entries
            if (
                area_matches(item, area)
                or str(item.get("id")) in pinned_ids
                or normalize(
                    item.get("name", "")
                ) in pinned_names
            )
        ]

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
                    "name",
                    "category",
                    "address",
                    "description",
                    "tags",
                    "question",
                    "keywords",
                )
            )
        )

        grams = {
            query[index:index + 2]
            for index in range(
                max(0, len(query) - 1)
            )
        }

        # 不是距離、路線或設施適合度評分。
        return sum(
            part in searchable for part in grams
        )

    pinned = [
        item for item in entries if required(item)
    ]
    others = [
        item for item in entries if not required(item)
    ]
    others.sort(key=score, reverse=True)

    selected = (
        pinned
        + others[:max(0, limit - len(pinned))]
    )

    return selected, {id(item) for item in pinned}


def pick(item, fields):
    return {
        key: item[key]
        for key in fields
        if key in item
        and item[key] not in ("", None, [], {})
    }


def attraction_summary(item, include_links):
    result = pick(
        item,
        (
            "id",
            "name",
            "category",
            "address",
            "opening_hours",
            "source_checked_on",
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
        item.get("source_url")
        and item.get("source_checked_on")
    )

    if include_links:
        result.update(
            pick(item, ("maps_url", "source_url"))
        )

    return result


def merchant_summary(item, include_links):
    result = pick(
        item,
        (
            "id",
            "name",
            "category",
            "address",
            "currency",
            "source_checked_on",
            "information_checked_on",
        ),
    )

    if item.get("description"):
        result["description"] = short(
            item["description"], 110
        )

    # 不把不同單位、套餐或房型混成價格區間。
    prices = [
        pick(price, ("name", "price", "unit"))
        for price in item.get("price_items", [])
        if isinstance(price, dict)
    ][:2]

    if prices:
        result["price_items"] = prices

    result["price_status"] = (
        "歷史參考；不代表總花費或即時售價"
    )

    if item.get("price_note"):
        result["price_note"] = short(
            item["price_note"], 140
        )

    if include_links:
        result.update(
            pick(
                item,
                (
                    "maps_url",
                    "source_url",
                    "information_source_url",
                    "website",
                    "official_url",
                    "booking_url",
                ),
            )
        )

    return result


def supplementary_summary(item, include_links):
    """農產與 FAQ 只保留基本資訊。"""
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

    for key in (
        "tags",
        "keywords",
        "months",
        "season_months",
    ):
        if isinstance(item.get(key), list):
            result[key] = item[key][:12]

    if include_links:
        result.update(
            pick(item, ("source_url", "maps_url"))
        )

    return result


def compact_context(raw, text, history=()):
    current = normalize(text)
    search_query = (
        text + " " + history_questions(history)
    )
    combined = normalize(search_query)
    area = requested_area(text, history)

    plan = raw.get("current_plan") or []

    if not isinstance(plan, list):
        raise ValueError("Invalid current plan")

    pinned_ids = [
        stop["id"]
        for stop in plan
        if stop.get("kind") == "attraction"
        and "id" in stop
    ]

    pinned_names = [
        stop["name"]
        for stop in plan
        if stop.get("kind") == "other"
        and stop.get("name")
    ]

    include_links = any(
        word in current
        for word in (
            "網址", "連結", "地圖", "導航",
            "官網", "訂房", "報名", "來源",
        )
    )

    planning = bool(plan) or any(
        word in combined
        for word in (
            "行程", "規劃", "一日遊", "半日遊",
            "兩天", "二天", "三天",
        )
    )

    result = {
        "notice": (
            "這是篩選後的候選資料，"
            "不代表完整清單或最適合選項。"
            "缺少欄位表示未知。介紹可能節錄。"
            "開放時間、價格、設施不是即時驗證結果。"
        ),
        "current_plan": plan,
        "area_scope": {
            "requested_area": area,
            "method": (
                "名稱、地址或明確地區欄位的"
                "文字比對；不是距離計算"
            ),
            "rule": (
                "有指定地區時，新推薦僅能使用"
                "area_match=true的候選。"
                "area_match=false僅供核對既有行程，"
                "不代表符合地區。"
                "候選不足就少排或詢問，"
                "不能自行擴大範圍或編造景點。"
                "新增範圍限制與舊行程衝突時先詢問，"
                "不擅自保留或刪除衝突站點。"
            ),
        },
    }

    # 預算不足時移除非必要候選。
    groups = []

    attraction_data = raw.get("attractions", {})
    attraction_rows = rows(attraction_data)

    named_attraction = any(
        len(normalize(item.get("name", ""))) >= 2
        and normalize(
            item.get("name", "")
        ) in current
        for item in attraction_rows
    )

    need_attractions = (
        planning
        or named_attraction
        or any(
            word in current
            for word in ("景點", "走走", "哪裡玩")
        )
    )

    result["attractions"] = {
        "status": attraction_data.get(
            "status", "missing"
        ),
        "items": [],
    }

    if need_attractions:
        chosen, pinned = select(
            attraction_rows,
            search_query,
            pinned_ids=pinned_ids,
            limit=MAX_CANDIDATES,
            area=area,
        )

        packed = [
            (
                area_note(
                    attraction_summary(
                        item, include_links
                    ),
                    item,
                    area,
                ),
                id(item) in pinned,
            )
            for item in chosen
        ]

        result["attractions"]["items"] = [
            item for item, _ in packed
        ]
        groups.append(
            (result["attractions"]["items"], packed)
        )

    merchants = rows(
        raw.get("merchants.json", [])
    )

    need_food = planning or any(
        word in current
        for word in (
            "餐廳", "吃", "午餐", "晚餐", "美食"
        )
    )

    need_lodging = any(
        word in combined
        for word in (
            "住宿", "民宿", "過夜", "訂房",
            "兩天", "二天", "三天",
        )
    )

    candidates = []
    normalized_pinned_names = {
        normalize(value) for value in pinned_names
    }

    for item in merchants:
        name = normalize(item.get("name", ""))
        category = str(item.get("category", ""))

        explicit = (
            name in normalized_pinned_names
            or (len(name) >= 2 and name in current)
        )

        if (
            explicit
            or (need_food and category == "餐廳")
            or (need_lodging and category == "民宿")
        ):
            candidates.append(item)

    merchant_packed = []

    categories = sorted({
        str(item.get("category", ""))
        for item in candidates
    })

    # 餐廳、住宿各最多8筆；地區不足不補其他區。
    for category in categories:
        chosen, pinned = select(
            [
                item for item in candidates
                if str(
                    item.get("category", "")
                ) == category
            ],
            search_query,
            pinned_names=pinned_names,
            limit=MAX_CANDIDATES,
            area=area,
        )

        merchant_packed.extend(
            (
                area_note(
                    merchant_summary(
                        item, include_links
                    ),
                    item,
                    area,
                ),
                id(item) in pinned,
            )
            for item in chosen
        )

    result["merchants.json"] = [
        item for item, _ in merchant_packed
    ]

    groups.append(
        (result["merchants.json"], merchant_packed)
    )

    for key, keywords in (
        (
            "local_products.json",
            (
                "農特產", "農產", "伴手禮",
                "當季", "產季", "水蜜桃", "甜柿",
            ),
        ),
        (
            "faq.json",
            (
                "系統", "使用說明", "怎麼用",
                "下載", "分享位置", "功能",
            ),
        ),
    ):
        entries = rows(raw.get(key, []))

        explicit = any(
            len(normalize(item.get("name", ""))) >= 2
            and normalize(
                item.get("name", "")
            ) in current
            for item in entries
        )

        if explicit or any(
            word in current for word in keywords
        ):
            chosen, _ = select(
                entries, text, limit=5
            )

            packed = [
                (
                    supplementary_summary(
                        item, include_links
                    ),
                    False,
                )
                for item in chosen
            ]

            result[key] = [
                item for item, _ in packed
            ]
            groups.append((result[key], packed))

    if any(
        word in current
        for word in ("活動", "市集", "祭典", "慶典")
    ):
        event_data = raw.get("events", {})

        result["events"] = {
            "status": event_data.get(
                "status", "unavailable"
            ),
            "as_of": event_data.get("as_of"),
            "notice": (
                "公告期間不代表每日有場次；"
                "報名與異動需確認。"
            ),
            "items": [],
        }

        packed = []

        for event in rows(event_data)[:3]:
            item = pick(
                event,
                (
                    "id",
                    "name",
                    "start_date",
                    "end_date",
                    "location",
                    "checked_on",
                ),
            )

            item["schedule_note"] = short(
                event.get("schedule_note", ""),
                160,
            )

            if include_links:
                item.update(
                    pick(event, ("source_url",))
                )

            packed.append((item, False))

        result["events"]["items"] = [
            item for item, _ in packed
        ]
        groups.append(
            (result["events"]["items"], packed)
        )

    else:
        result["events"] = {
            "status": "not_selected",
            "items": [],
            "notice": (
                "本次未提供活動資料，"
                "不可沿用歷史活動推薦。"
            ),
        }

    while len(json_text(result)) > MAX_CONTEXT_CHARS:
        removed = False

        for target, packed in sorted(
            groups,
            key=lambda group: len(group[0]),
            reverse=True,
        ):
            for index in range(
                len(packed) - 1, -1, -1
            ):
                item, required = packed[index]

                if not required:
                    packed.pop(index)
                    target[:] = [
                        entry for entry, _ in packed
                    ]
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
    result["attractions"]["total_count"] = len(
        attraction_rows
    )

    # 計數欄位也算入限制。
    if len(json_text(result)) > MAX_CONTEXT_CHARS:
        result["attractions"].pop(
            "selected_count", None
        )
        result["attractions"].pop(
            "total_count", None
        )

    return result


if __name__ == "__main__":
    from .openai_reply import build_context
    from .attraction_context import load_attraction_context
    from .events import event_context

    raw = build_context()
    raw["attractions"] = load_attraction_context()
    raw["events"] = event_context()
    raw["current_plan"] = []

    question = (
        "從桃園開車，兩位大人，"
        "安排角板山周邊一日遊，推薦午餐"
    )

    compact = compact_context(raw, question)

    print("原始參考資料字數：", len(json_text(raw)))
    print("精簡參考資料字數：", len(json_text(compact)))
    print(
        "指定地區：",
        compact["area_scope"]["requested_area"],
    )

    print("\n景點候選：")
    for item in compact["attractions"]["items"]:
        print("・", item.get("name"))

    print("\n商家候選：")
    for item in compact["merchants.json"]:
        print("・", item.get("name"))

    print("\n含FAQ：", "faq.json" in compact)
    print("含農特產：", "local_products.json" in compact)