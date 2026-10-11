"""查詢本機餐廳與民宿資料，回傳文字供 LINE 整合使用。"""

import json
import unicodedata
from pathlib import Path
from urllib.parse import quote


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "merchants.json"


def normalize(text):
    return "".join(
        unicodedata.normalize("NFKC", text).casefold().split()
    )


def load_merchants(data_path=None):
    """讀取並驗證商家資料。"""
    path = Path(data_path) if data_path is not None else DATA_PATH

    with path.open("r", encoding="utf-8-sig") as file:
        merchants = json.load(file)

    if not isinstance(merchants, list):
        raise ValueError("商家資料必須為陣列")

    seen_ids = set()

    for merchant in merchants:
        if not isinstance(merchant, dict):
            raise ValueError("每筆商家資料必須為物件")

        for field in ("id", "name", "category", "address"):
            value = merchant.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"缺少有效欄位：{field}")

        if merchant["id"] in seen_ids:
            raise ValueError("商家 id 不可重複")
        seen_ids.add(merchant["id"])

        tags = merchant.get("tags", [])
        if not isinstance(tags, list) or not all(
            isinstance(tag, str) for tag in tags
        ):
            raise ValueError("tags 必須為文字陣列")

        for field in (
            "description",
            "price_note",
            "opening_hours",
            "opening_hours_note",
            "opening_hours_source",
            "opening_hours_checked_on",
            "source_checked_on",
            "information_checked_on",
            "currency",
        ):
            value = merchant.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{field} 必須為文字或 null")

        for field in (
            "maps_url",
            "source_url",
            "information_source_url",
        ):
            value = merchant.get(field)
            if value is not None and (
                not isinstance(value, str)
                or not value.startswith("https://")
            ):
                raise ValueError(f"{field} 必須為 HTTPS 網址")

        prices = merchant.get("price_items", [])
        if not isinstance(prices, list):
            raise ValueError("price_items 必須為陣列")

        for item in prices:
            if not isinstance(item, dict):
                raise ValueError("價格項目必須為物件")

            for field in ("name", "unit"):
                value = item.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("價格項目缺少名稱或單位")

            price = item.get("price")
            if (
                isinstance(price, bool)
                or not isinstance(price, int)
                or price < 0
            ):
                raise ValueError("價格必須為非負整數")

    return merchants



def format_lodging(merchant):
    """住宿專用排版；未收錄房價時提供查價入口。"""
    lines = ["🏡 今晚，住進山裡吧！", merchant["name"],
             f"\n📍 住宿地址\n{merchant['address']}"]
    if merchant.get("description"):
        lines.append(f"\n🌿 這裡的小亮點\n{merchant['description']}")
    prices = merchant.get("price_items", [])
    currency = merchant.get("currency") or "TWD"
    lines.append(f"\n💰 住宿參考價（{currency}）")
    for item in prices[:5]:
        lines.append(f"・{item['name']}｜{item['price']:,} 元／{item['unit']}")
    if len(prices) > 5:
        lines.append("更多房型價格，請查看下方來源。")
    if merchant.get("price_note"):
        lines.append(merchant["price_note"])
    elif not prices:
        lines.append("選好日期與人數，再向業者確認房價吧！")
    source = merchant.get("source_url")
    if source:
        label = ("🔎 官方旅遊資訊｜房型與聯絡方式" if merchant.get("source_kind") == "tourism"
                 else "🏡 民宿官網｜房型、價格與訂房資訊")
        lines.append(f"\n{label}\n" + quote(source, safe=":/?=&%"))
    if merchant.get("maps_url"):
        lines.append("\n🧭 帶我去這裡（Google Maps）\n" + quote(merchant["maps_url"], safe=":/?=&%"))
    checked = merchant.get("source_checked_on") or merchant.get("information_checked_on")
    if checked:
        lines.append(f"\n🗓 資料查詢日期：{checked}")
    lines.append("\n💛 出發前小提醒\n房價與空房以業者確認為準；喜歡的話，記得自行聯絡訂房喔！")
    return "\n".join(lines)


def format_merchant(merchant):
    """依商家類型顯示特色、參考價格、地圖與來源。"""
    is_lodging = merchant["category"] == "民宿"
    if is_lodging:
        return format_lodging(merchant)

    lines = [
        merchant["name"],
        f"類型：{merchant['category']}",
        f"地址：{merchant['address']}",
    ]

    if merchant.get("description"):
        lines.append(f"\n特色：{merchant['description']}")

    prices = merchant.get("price_items", [])
    if prices:
        currency = merchant.get("currency") or "TWD"

        if is_lodging:
            lines.append(
                f"\n住宿參考價格（{currency}，"
                "計價單位請見各房型）："
            )
        else:
            lines.append(
                f"\n參考價格（{currency}，"
                "計價單位請見各品項）："
            )

        for item in prices[:5]:
            lines.append(
                f"・{item['name']}："
                f"{item['price']} 元／{item['unit']}"
            )

        if len(prices) > 5:
            lines.append("以上列出前 5 項，其他價格請查看來源。")

    if merchant.get("price_note"):
        lines.append(f"\n價格說明：{merchant['price_note']}")

    if merchant.get("source_checked_on"):
        lines.append(
            "價格來源查詢日期："
            + merchant["source_checked_on"]
        )

    maps_url = merchant.get("maps_url")
    if maps_url:
        if is_lodging:
            maps_label = "📍 查看住宿位置與導航（Google Maps）："
        else:
            maps_label = "📍 查看營業時間與導航（Google Maps）："

        lines.append(
            f"\n{maps_label}\n"
            + quote(maps_url, safe=":/?=&%")
        )

    source_url = merchant.get("source_url")
    if source_url:
        if is_lodging:
            source_label = "🏡 民宿官網｜房型、價格與訂房資訊："
        else:
            source_label = "📋 查看餐點與價格來源："

        lines.append(
            f"\n{source_label}\n"
            + quote(source_url, safe=":/?=&%")
        )

    if is_lodging:
        lines.append(
            "\n房價依入住日期、房型及方案而異。"
            "訂房前請向業者確認最終價格與空房，"
            "以上資訊不代表已完成預訂。"
        )
    else:
        lines.append("\n營業時間與價格以店家最新公告為準。")

    return "\n".join(lines)


def get_merchant_reply(text="", *, data_path=None):
    """回傳商家資訊，不判定即時營業狀態或住宿空房。"""
    if not isinstance(text, str):
        raise TypeError("輸入必須為字串")

    if len(text) > 2000:
        return "問題太長了，請縮短至 2000 字以內。"

    try:
        merchants = load_merchants(data_path)
    except (OSError, ValueError):
        return (
            "商家資料暫時無法讀取，請稍後再試，"
            "或通知專題管理者。"
        )

    if not merchants:
        return "目前尚未提供商家資料。"

    query = normalize(text)

    categories = {
        "餐廳": "餐廳",
        "推薦餐廳": "餐廳",
        "找餐廳": "餐廳",
        "美食": "餐廳",
        "推薦美食": "餐廳",
        "民宿": "民宿",
        "推薦民宿": "民宿",
        "住宿": "民宿",
    }

    if query in {"", "商家", "在地商家", "商家列表"}:
        matches = merchants
    elif query in categories:
        matches = [
            merchant
            for merchant in merchants
            if merchant["category"] == categories[query]
        ]
    else:
        matches = [
            merchant
            for merchant in merchants
            if query in normalize(merchant["name"])
            or normalize(merchant["name"]) in query
        ]

    if not matches:
        return (
            "目前資料中找不到符合的商家。"
            "可輸入「餐廳」「民宿」或店家名稱查詢；"
            "沒有查到不代表當地沒有這類商家。"
        )

    # 多筆結果先顯示清單，避免 LINE 訊息過長。
    if len(matches) > 1:
        lodging_only = all(m["category"] == "民宿" for m in matches)
        limit = 20 if lodging_only else 10
        lines = ([f"🏡 山裡住一晚｜{len(matches)} 家民宿口袋名單", "慢慢挑一間，替旅程留個舒服的落腳處 🌿"]
                 if lodging_only else ["符合的商家："])

        for merchant in matches[:limit]:
            lines.append(
                f"・{merchant['name']}（{merchant['category']}）"
            )

        if len(matches) > limit:
            lines.append(
                f"目前只顯示前 {limit} 筆，"
                "可輸入「餐廳」或「民宿」縮小範圍。"
            )

        lines.append("\n💬 喜歡哪一家？輸入完整店名，看看特色、房價與訂房資訊！" if lodging_only else "請輸入店家名稱查看詳細資訊。")
        return "\n".join(lines)

    return format_merchant(matches[0])


if __name__ == "__main__":
    print(get_merchant_reply("餐廳"))