"""餐廳分類、餐廳與民宿字卡；只使用本機資料。"""

import re
import unicodedata
from urllib.parse import quote, urlsplit

from linebot.v3.messaging import FlexMessage, FlexContainer, TextMessage

from .merchant_service import load_merchants, format_merchant


PAGE_SIZE = 8

FOOD_GROUPS = {
    "泰雅風味": {
        "label": "🌿 泰雅／原住民風味",
        "tags": {"泰雅風味", "原住民風味"},
    },
    "山產合菜": {
        "label": "🍲 山產／合菜／熱炒",
        "tags": {"山產", "合菜", "快炒", "熱炒"},
    },
    "麵飯便餐": {
        "label": "🍜 麵飯／便餐",
        "tags": {"牛肉麵", "麵食", "便餐", "簡餐", "獵人餐"},
    },
    "咖啡西餐": {
        "label": "☕ 咖啡／西式餐點",
        "tags": {"景觀咖啡", "咖啡", "西式排餐"},
    },
    "火鍋火烤": {
        "label": "🔥 火鍋／火烤",
        "tags": {"火鍋", "火烤兩吃"},
    },
    "早餐": {
        "label": "🌅 早餐",
        "tags": {"早餐"},
    },
    "全部": {
        "label": "🍽️ 全部餐廳",
        "tags": set(),
    },
}


def normalize(text):
    return "".join(
        char
        for char in unicodedata.normalize("NFKC", text).casefold()
        if not char.isspace()
        and not unicodedata.category(char).startswith("P")
    )


def text_item(text, *, size="sm", color="#374151", bold=False):
    item = {
        "type": "text",
        "text": str(text) or "—",
        "size": size,
        "color": color,
        "wrap": True,
    }
    if bold:
        item["weight"] = "bold"
    return item


def message_button(label, text, *, primary=False):
    button = {
        "type": "button",
        "height": "sm",
        "style": "primary" if primary else "link",
        "action": {
            "type": "message",
            "label": label,
            "text": text,
        },
    }
    if primary:
        button["color"] = "#237A65"
    return button


def safe_url(value):
    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()
    if any(ord(char) < 32 for char in value):
        return None

    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            return None
    except ValueError:
        return None

    encoded = quote(value, safe=":/?=&%#@+;,~-._")
    return encoded if len(encoded) <= 2000 else None


def uri_button(label, value):
    url = safe_url(value)
    if not url:
        return None

    return {
        "type": "button",
        "height": "sm",
        "style": "link",
        "action": {
            "type": "uri",
            "label": label,
            "uri": url,
        },
    }


def flex_message(title, contents):
    return FlexMessage(
        alt_text=title[:100],
        contents=FlexContainer.from_dict(contents),
    )


def restaurants_in_group(merchants, group):
    if group not in FOOD_GROUPS:
        raise ValueError("Unknown restaurant group")

    restaurants = [
        item for item in merchants
        if item["category"] == "餐廳"
    ]
    if group == "全部":
        return restaurants

    wanted = FOOD_GROUPS[group]["tags"]
    return [
        item for item in restaurants
        if wanted.intersection(item.get("tags", []))
    ]


def make_food_menu(merchants):
    contents = [
        text_item("🍽️ 今天想吃什麼？", size="xl", bold=True),
        text_item("選一種口味，看看山裡的餐廳吧 🌿"),
    ]

    for group, config in FOOD_GROUPS.items():
        count = len(restaurants_in_group(merchants, group))
        if not count:
            continue

        contents.append(
            message_button(
                f"{config['label']}（{count}）",
                f"餐廳分類：{group}｜第1頁",
            )
        )

    if not any(item["category"] == "餐廳" for item in merchants):
        return TextMessage(text="🌿 餐廳資料準備中，請稍後再試。")

    contents.append(
        text_item(
            "同一家餐廳可能提供多種料理，會出現在不同分類。",
            size="xs",
            color="#6B7280",
        )
    )

    return flex_message(
        "今天想吃什麼？選擇餐廳類型",
        {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": contents,
            },
        },
    )


def create_merchant_bubble(merchant):
    lodging = merchant["category"] == "民宿"
    heading = "🏡 山裡住一晚" if lodging else "🍽️ 山裡吃一餐"
    description = merchant.get("description") or "點選詳細介紹，看看店家資訊。"

    # 字卡先顯示短介紹；完整內容保留在詳細介紹。
    if len(description) > 100:
        description = description[:99] + "…"

    contents = [
        text_item(heading, color="#237A65", bold=True),
        text_item(merchant["name"], size="xl", bold=True),
    ]

    tags = merchant.get("tags", [])
    if tags:
        contents.append(
            text_item(" · ".join(tags[:3]), size="xs", color="#6B7280")
        )

    contents.extend([
        text_item(description),
        text_item("📍 " + merchant["address"], size="xs"),
    ])

    prices = merchant.get("price_items", [])
    if prices:
        # 只展示一個具名品項，避免把菜價誤當每人餐費。
        item = prices[0]
        currency = merchant.get("currency") or "TWD"
        contents.append(
            text_item(
                f"💰 歷史參考（{currency}）\n"
                f"{item['name']}：{item['price']:,} 元／{item['unit']}",
                bold=True,
            )
        )

        # 保留已調漲、服務費、平假日等限制，不只留下數字。
        note = merchant.get("price_note")
        if note:
            contents.append(text_item(note, size="xs", color="#6B7280"))

        checked = (
            merchant.get("source_checked_on")
            or merchant.get("information_checked_on")
        )
        if checked:
            contents.append(
                text_item(
                    f"資料查詢：{checked}，不代表價格更新日期",
                    size="xs",
                    color="#6B7280",
                )
            )
    else:
        contents.append(
            text_item(
                "💰 房價請依日期與人數向業者確認"
                if lodging
                else "💰 消費參考請點「詳細介紹」查看",
                size="xs",
                color="#6B7280",
            )
        )

    contents.append(
        text_item(
            "房價、空房與訂房方式請向業者確認。"
            if lodging
            else "餐點、營業時間與價格以店家公告為準。",
            size="xs",
            color="#6B7280",
        )
    )

    buttons = [
        message_button(
            "📖 詳細介紹",
            f"商家詳細：{merchant['name']}",
            primary=True,
        )
    ]

    map_url = safe_url(merchant.get("maps_url"))
    if not map_url:
        map_url = "https://www.google.com/maps/search/?api=1&query=" + quote(merchant["name"] + " " + merchant.get("address", ""))
    map_button = uri_button("📍 Google Maps", map_url)
    if map_button:
        buttons.append(map_button)

    source_kind = merchant.get("source_kind")
    if source_kind == "official":
        source_label = "🏡 官網／房型資訊" if lodging else "🌐 店家官網"
    elif source_kind == "tourism":
        source_label = "🔎 官方旅遊資訊"
    else:
        source_label = "📋 查看資料來源"

    source_button = uri_button(source_label, merchant.get("source_url"))
    if source_button:
        buttons.append(source_button)

    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": contents,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": buttons,
        },
    }


def page_command(kind, group, page):
    if kind == "民宿":
        return f"民宿列表：第{page}頁"
    return f"餐廳分類：{group}｜第{page}頁"


def make_listing(merchants, *, kind, group="全部", page=1):
    if kind == "民宿":
        matches = [
            item for item in merchants
            if item["category"] == "民宿"
        ]
        title = "🏡 山裡住一晚"
    else:
        matches = restaurants_in_group(merchants, group)
        title = FOOD_GROUPS[group]["label"]

    if not matches:
        return TextMessage(text="🌿 這個分類目前沒有資料，可以試試其他分類。")

    total_pages = (len(matches) + PAGE_SIZE - 1) // PAGE_SIZE
    if not 1 <= page <= total_pages:
        return TextMessage(
            text=f"這份清單共有 {total_pages} 頁，請輸入「餐廳」或「民宿」重新選擇。"
        )

    start = (page - 1) * PAGE_SIZE
    selected = matches[start:start + PAGE_SIZE]
    bubbles = [create_merchant_bubble(item) for item in selected]

    navigation = []
    if page > 1:
        navigation.append(
            message_button(
                "← 上一頁",
                page_command(kind, group, page - 1),
            )
        )
    if page < total_pages:
        navigation.append(
            message_button(
                "下一頁 →",
                page_command(kind, group, page + 1),
                primary=True,
            )
        )
    navigation.append(
        message_button("🍽️ 換個餐廳分類", "餐廳")
    )
    navigation.append(
        message_button("🏡 看民宿", "民宿")
    )

    # 第九張是翻頁卡；每頁最多八張店家卡。
    bubbles.append({
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                text_item(title, size="xl", bold=True),
                text_item(f"第 {page}／{total_pages} 頁"),
                text_item(
                    f"共 {len(matches)} 家\n"
                    f"這頁顯示第 {start + 1}～{start + len(selected)} 家"
                ),
                text_item(
                    "左右滑動看店家，或按下面的按鈕繼續逛。",
                    color="#6B7280",
                ),
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": navigation,
        },
    })

    return flex_message(
        f"{title}｜第{page}頁，共{len(matches)}家",
        {"type": "carousel", "contents": bubbles},
    )


def merchant_keyword(text):
    query = normalize(text)
    for prefix in (
        "可以介紹一下", "可以介紹", "請介紹一下", "幫我介紹",
        "我想了解", "我想看", "介紹一下", "請介紹",
        "介紹", "查詢", "查看", "看看", "看",
    ):
        if query.startswith(prefix):
            query = query[len(prefix):]
            break

    for suffix in (
        "的詳細介紹", "的介紹", "的字卡", "的卡片",
        "的地圖", "的導航", "詳細介紹", "介紹",
        "字卡", "卡片", "地圖", "導航",
    ):
        if query.endswith(suffix):
            query = query[:-len(suffix)]
            break
    return query


def get_merchant_message(text):
    """只攔截明確的選單、翻頁、詳細介紹及完整店名。"""
    if not isinstance(text, str) or not text.strip() or len(text) > 2000:
        return None

    raw = unicodedata.normalize("NFKC", text).strip()
    query = normalize(raw)

    food_menu = query in {
        "餐廳", "推薦餐廳", "找餐廳", "美食", "推薦美食", "餐廳分類",
    }
    lodging_list = query in {"民宿", "住宿", "推薦民宿"}
    all_restaurants = query == "全部餐廳"

    food_page = re.fullmatch(
        r"餐廳分類[:：](.+?)[|｜]第([0-9]{1,4})頁", raw
    )
    lodging_page = re.fullmatch(
        r"民宿列表[:：]第([0-9]{1,4})頁", raw
    )
    detail = re.fullmatch(r"商家詳細[:：](.+)", raw)

    # 一般句子僅做完整店名匹配，不把行程、求救或附近問題截走。
    merchants = load_merchants()

    if food_menu:
        return make_food_menu(merchants)
    if lodging_list:
        return make_listing(merchants, kind="民宿")
    if all_restaurants:
        return make_listing(merchants, kind="餐廳")

    if food_page:
        group = food_page.group(1)
        if group not in FOOD_GROUPS:
            return TextMessage(text="請輸入「餐廳」，重新選擇餐點類型。")
        return make_listing(
            merchants,
            kind="餐廳",
            group=group,
            page=int(food_page.group(2)),
        )

    if lodging_page:
        return make_listing(
            merchants,
            kind="民宿",
            page=int(lodging_page.group(1)),
        )

    keyword = normalize(detail.group(1)) if detail else merchant_keyword(raw)
    matches = [
        item for item in merchants
        if normalize(item["name"]) == keyword
    ]
    if not matches:
        if detail:
            return TextMessage(text="🌿 店家資料可能已更新，請重新選擇餐廳或民宿。")
        return None

    if len(matches) != 1:
        return TextMessage(text="🌿 店名有重複資料，請通知管理者確認。")

    if detail:
        answer = format_merchant(matches[0])
        # 以 UTF-16 計算，避免超過 LINE 文字訊息限制。
        if len(answer.encode("utf-16-le")) // 2 > 4400:
            return TextMessage(text="🌿 店家介紹較長，請先使用字卡上的資料來源查看。")
        return TextMessage(text=answer)

    return flex_message(
        f"店家介紹｜{matches[0]['name']}",
        create_merchant_bubble(matches[0]),
    )