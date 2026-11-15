"""專題折扣商品展示頁：無金流、無會員、無訂單寫入。"""

from flask import Blueprint, abort, jsonify, make_response, render_template, request

from modules.coupon.coupon_service import calculate_discount, get_coupon, is_expired

coupon_web = Blueprint("coupon_web", __name__)


def _get_coupon_or_404(coupon_id):
    if not coupon_id.startswith("coupon_") or len(coupon_id) > 50:
        abort(404)
    try:
        coupon = get_coupon(coupon_id)
    except (OSError, ValueError):
        abort(503)
    if coupon is None:
        abort(404)
    return coupon


def _qty(value):
    # 最多十件。絕不對使用者傳入的原價／折扣數字採信。
    if not isinstance(value, str) or not value.isdecimal():
        return None
    quantity = int(value)
    return quantity if 1 <= quantity <= 10 else None


def _private(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@coupon_web.get("/coupon/shop/<coupon_id>")
def show_coupon_product(coupon_id):
    coupon = _get_coupon_or_404(coupon_id)
    quote = calculate_discount(coupon, quantity=1)
    color_theme = {
        "coupon_001": ("agri", "🍑", "山林農產"),
        "coupon_002": ("gift", "🎁", "旅途伴手禮"),
        "coupon_003": ("culture", "🌿", "在地文化體驗"),
    }.get(coupon_id, ("agri", "🎟", "復興好禮"))
    return _private(make_response(render_template(
        "coupon_shop.html", coupon=coupon, quote=quote,
        expired=is_expired(coupon), theme=color_theme[0],
        motif=color_theme[1], product_label=color_theme[2],
    )))


@coupon_web.get("/api/coupon/quote/<coupon_id>")
def coupon_quote(coupon_id):
    coupon = _get_coupon_or_404(coupon_id)
    if is_expired(coupon):
        return _private(jsonify(error="這項優惠已超過展示期限")), 410
    quantity = _qty(request.args.get("quantity", "1"))
    if quantity is None:
        return _private(jsonify(error="數量必須在 1 到 10 之間")), 400
    return _private(jsonify(calculate_discount(coupon, quantity=quantity)))


@coupon_web.post("/api/coupon/complete/<coupon_id>")
def complete_coupon_demo(coupon_id):
    coupon = _get_coupon_or_404(coupon_id)
    if is_expired(coupon):
        return _private(jsonify(error="這項優惠已超過展示期限")), 410
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _private(jsonify(error="請提供有效的商品數量")), 400
    # 只接受商品數量，忽略客戶端提交的價格／折扣，避免錯價。
    quantity = _qty(str(body.get("quantity", ""))) if type(body.get("quantity")) is int else None
    if quantity is None:
        return _private(jsonify(error="數量必須在 1 到 10 之間")), 400
    quote = calculate_discount(coupon, quantity=quantity)
    return _private(jsonify({
        "status": "demo_complete",
        "message": "展示完成，未成立訂單或付款，也沒有向商家核銷。",
        "product_name": coupon["product_name"],
        "quantity": quantity,
        "quote": quote,
    }))
