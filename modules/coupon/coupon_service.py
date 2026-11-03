"""優惠券資料讀取與驗證。"""

import json
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COUPON_DATA_PATH = PROJECT_ROOT / "data" / "coupons.json"

REQUIRED_FIELDS = {
    "id",
    "title",
    "category",
    "discount_text",
    "description",
    "conditions",
    "valid_until",
    "demo_only",
}


def _validate_coupon(item):
    if not isinstance(item, dict):
        raise ValueError("優惠券資料必須為 JSON object")

    missing = REQUIRED_FIELDS - set(item)
    if missing:
        raise ValueError(
            "優惠券缺少欄位：" + ", ".join(sorted(missing))
        )

    for key in (
        "id",
        "title",
        "category",
        "discount_text",
        "description",
        "conditions",
        "valid_until",
    ):
        if not isinstance(item[key], str) or not item[key].strip():
            raise ValueError(f"優惠券欄位 {key} 不可為空")

    if item["demo_only"] is not True:
        raise ValueError("目前優惠券只能使用 demo_only=true 的示範資料")

    try:
        date.fromisoformat(item["valid_until"])
    except ValueError as exc:
        raise ValueError("valid_until 必須為 YYYY-MM-DD") from exc


def load_coupons(data_path=None):
    path = Path(data_path) if data_path else COUPON_DATA_PATH

    with path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("coupons.json 必須為 JSON array")

    seen = set()
    coupons = []

    for item in data:
        _validate_coupon(item)

        coupon_id = item["id"].strip()
        if coupon_id in seen:
            raise ValueError(f"優惠券 id 重複：{coupon_id}")

        seen.add(coupon_id)
        coupons.append(dict(item))

    return coupons


def get_coupon(coupon_id, data_path=None):
    if not isinstance(coupon_id, str) or not coupon_id.strip():
        return None

    coupon_id = coupon_id.strip()

    for coupon in load_coupons(data_path):
        if coupon["id"] == coupon_id:
            return coupon

    return None


def is_expired(coupon, today=None):
    if not isinstance(coupon, dict):
        return True

    current = today or date.today()

    try:
        expires = date.fromisoformat(coupon["valid_until"])
    except (KeyError, TypeError, ValueError):
        return True

    return current > expires
