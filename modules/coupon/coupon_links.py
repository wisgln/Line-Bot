"""LINE 優惠券與網站的 HTTPS 連結；Preview 不指向 production。"""

import os
from urllib.parse import quote, urlsplit


def _https_origin(value):
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    if "://" not in value:
        value = "https://" + value
    parts = urlsplit(value)
    if (parts.scheme != "https" or not parts.hostname or parts.username
            or parts.password or parts.path not in ("", "/")
            or parts.query or parts.fragment):
        return None
    return f"https://{parts.netloc}"


def get_coupon_shop_url(coupon_id):
    """沒有可信 HTTPS 部署網址時回 None，保留 LINE 內試算備援。"""
    if not isinstance(coupon_id, str) or not coupon_id.strip():
        return None

    # 由整合者設定的 HTTPS 網址優先；不得混入路徑或 query。
    origin = _https_origin(os.getenv("COUPON_PUBLIC_BASE_URL"))
    if origin is None:
        # VERCEL_URL 需啟用 Vercel 自動系統環境變數。
        generated = os.getenv("VERCEL_URL", "").strip()
        if generated.endswith(".vercel.app"):
            origin = _https_origin(generated)

    if origin is None:
        # Vercel 若未公開系統變數，可用目前 webhook 的可信 Vercel 網域。
        # 不採用任意 Host，避免讓不可信網域出現在 LINE 卡片。
        try:
            from flask import has_request_context, request
            if has_request_context():
                host = request.host.lower()
                if host.endswith(".vercel.app") and ":" not in host:
                    origin = f"https://{host}"
        except RuntimeError:
            pass

    if origin is None:
        # 本機/不可信網域時保留 LINE 內試算，不輸出無效的 HTTP URL。
        return None

    return f"{origin}/coupon/shop/{quote(coupon_id, safe='')}"
