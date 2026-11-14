"""示範優惠資料與優惠計算：不建立真實訂單或付款。"""

import json
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COUPON_DATA_PATH = PROJECT_ROOT / "data" / "coupons.json"

REQUIRED_FIELDS = {
    "id", "title", "category", "discount_text", "description",
    "conditions", "valid_until", "demo_only", "product_name",
    "original_price", "discount_type", "discount_value", "min_spend",
}


def _validate_coupon(item):
    if not isinstance(item, dict):
        raise ValueError("優惠券資料必須為 JSON object")

    missing = REQUIRED_FIELDS - set(item)
    if missing:
        raise ValueError("優惠券缺少欄位：" + ", ".join(sorted(missing)))

    for key in (
        "id", "title", "category", "discount_text", "description",
        "conditions", "valid_until", "product_name",
    ):
        if not isinstance(item[key], str) or not item[key].strip():
            raise ValueError(f"優惠券欄位 {key} 不可為空")

    if item["demo_only"] is not True:
        raise ValueError("目前只支援 demo_only=true 的專題示範資料")

    try:
        date.fromisoformat(item["valid_until"])
    except ValueError as exc:
        raise ValueError("valid_until 必須為 YYYY-MM-DD") from exc

    for field in ("original_price", "discount_value", "min_spend"):
        value = item[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} 必須為非負整數")

    if item["original_price"] <= 0:
        raise ValueError("original_price 必須大於零")

    if item["discount_type"] not in {"fixed", "percent"}:
        raise ValueError("discount_type 必須是 fixed 或 percent")

    if item["discount_type"] == "percent" and item["discount_value"] > 100:
        raise ValueError("百分比折扣不得超過 100")


def load_coupons(data_path=None):
    path = Path(data_path) if data_path is not None else COUPON_DATA_PATH
    with path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("coupons.json 必須為 JSON array")

    seen = set()
    coupons = []
    for item in data:
        _validate_coupon(item)
        if item["id"] in seen:
            raise ValueError(f"優惠券 id 重複：{item['id']}")
        seen.add(item["id"])
        coupons.append(dict(item))
    return coupons


def get_coupon(coupon_id, data_path=None):
    if not isinstance(coupon_id, str) or not coupon_id.strip():
        return None
    return next(
        (item for item in load_coupons(data_path) if item["id"] == coupon_id.strip()),
        None,
    )


def is_expired(coupon, today=None):
    if not isinstance(coupon, dict):
        return True
    try:
        return (today or date.today()) > date.fromisoformat(coupon["valid_until"])
    except (KeyError, TypeError, ValueError):
        return True


def calculate_discount(coupon):
    """對 coupons.json 定義的單件示例商品計算折後價，皆為新臺幣整數。"""
    _validate_coupon(coupon)
    original = coupon["original_price"]
    if original < coupon["min_spend"]:
        discount = 0
    elif coupon["discount_type"] == "fixed":
        discount = min(original, coupon["discount_value"])
    else:
        discount = original * coupon["discount_value"] // 100
    return {
        "original": original,
        "discount": discount,
        "total": original - discount,
    }
