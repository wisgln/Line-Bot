"""固定問題本機回答；AI 僅接收少量候選與必要行程資料。"""

import copy
import json
import re

from .compact_context import ContextBudgetError
from .intent import normalize


def local_lookup(text, faq_path=None):
    from .faq import find_answer, load_faq
    from .attraction_context import load_attraction_context
    from modules.merchant.merchant_service import (
        load_merchants,
        get_merchant_reply,
    )
    from .local_products import get_local_products_reply

    query = normalize(text)

    try:
        answer = find_answer(text, load_faq(faq_path))
        if answer is not None:
            return answer
    except (OSError, ValueError):
        pass

    try:
        merchants = load_merchants()
    except (OSError, ValueError):
        merchants = []

    categories = {
        "餐廳": "餐廳",
        "推薦餐廳": "餐廳",
        "餐廳營業時間": "餐廳",
        "民宿": "民宿",
        "推薦民宿": "民宿",
        "住宿": "民宿",
        "商家": "商家",
        "在地商家": "商家",
    }

    if query in categories:
        return get_merchant_reply(categories[query])

    for item in merchants:
        if query == normalize(item["name"]):
            return get_merchant_reply(item["name"])

    hours_words = (
        "幾點關",
        "幾點開",
        "營業時間",
        "開放時間",
        "何時關",
        "何時開",
    )

    if any(word in text for word in hours_words):
        named = [
            item
            for item in merchants
            if normalize(item["name"]) in query
        ]

        if len(named) == 1:
            return get_merchant_reply(named[0]["name"])

        keyword = re.sub(
            r"幾點關門|幾點關|幾點開門|幾點開|"
            r"營業時間|開放時間|何時關門|何時開門|"
            r"請問|的|是|嗎",
            "",
            query,
        )

        rows = (
            load_attraction_context().get("items", [])
            + merchants
        )

        matches = [
            item
            for item in rows
            if (
                len(keyword) >= 2
                and (
                    keyword in normalize(item["name"])
                    or normalize(item["name"]) in keyword
                )
            )
        ]

        if len(matches) != 1:
            if matches:
                return (
                    "想查哪一個地點的時間？\n"
                    + "\n".join(
                        "・" + item["name"]
                        for item in matches[:5]
                    )
                )

            return (
                "請提供景點或店家完整名稱，"
                "我幫你查已收錄的時間。"
            )

        item = matches[0]
        hours = item.get("opening_hours")

        if not hours:
            return (
                f"目前未收錄{item['name']}的營業／開放時間，"
                "建議向景點或店家確認後再出發。"
            )

        return (
            f"{item['name']}\n"
            f"目前資料記載：{hours}\n"
            "實際時間可能調整，出發前請向景點或店家確認。"
        )

    return get_local_products_reply(text)


def small_context(context, text):
    result = copy.deepcopy(context)
    plan = result.get("current_plan", [])

    ids = {
        str(stop.get("id"))
        for stop in plan
        if stop.get("kind") == "attraction"
    }

    names = {
        stop.get("name")
        for stop in plan
    }

    groups = [
        result.get("attractions", {}).get("items", []),
        result.get("merchants.json", []),
    ]

    # 新增候選總計最多5筆。
    # 舊站點另外保留，供行程修改及資料驗證使用。
    kept = [[], []]
    fresh = 0

    maximum = max(
        (len(group) for group in groups),
        default=0,
    )

    for index in range(maximum):
        for group_index, group in enumerate(groups):
            if index >= len(group):
                continue

            item = group[index]

            pinned = (
                (
                    group_index == 0
                    and str(item.get("id")) in ids
                )
                or item.get("name") in names
            )

            if pinned or fresh < 5:
                kept[group_index].append(item)

                if not pinned:
                    fresh += 1

    result.setdefault("attractions", {})["items"] = kept[0]
    result["merchants.json"] = kept[1]

    if not any(
        word in text
        for word in ("活動", "祭", "節慶")
    ):
        result.pop("events", None)

    if not any(
        word in text
        for word in (
            "使用",
            "功能",
            "系統",
            "操作",
            "怎麼用",
        )
    ):
        result.pop("faq.json", None)

    if not any(
        word in text
        for word in (
            "農特產",
            "農產",
            "水蜜桃",
            "甜柿",
            "香菇",
            "竹筍",
        )
    ):
        result.pop("local_products.json", None)

    def size():
        return len(
            json.dumps(result, ensure_ascii=False)
        )

    while size() > 6000:
        removed = False

        for group_index, group in enumerate(kept):
            for i in range(len(group) - 1, -1, -1):
                item = group[i]

                pinned = (
                    (
                        group_index == 0
                        and str(item.get("id")) in ids
                    )
                    or item.get("name") in names
                )

                if not pinned:
                    group.pop(i)
                    removed = True
                    break

            if removed:
                break

        if not removed:
            raise ContextBudgetError(
                "Required context exceeds budget"
            )

    return result