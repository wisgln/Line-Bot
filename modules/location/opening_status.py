from datetime import datetime, timedelta, timezone
import re


# Vercel 的伺服器使用 UTC，營業狀態一律以台灣時間（UTC+8）判斷。
TAIWAN_TZ = timezone(timedelta(hours=8))

WEEKDAY_NAMES = {
    0: "一",
    1: "二",
    2: "三",
    3: "四",
    4: "五",
    5: "六",
    6: "日",
}

TIME_RANGE = r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})"


def _to_minutes(time_text):
    hour, minute = map(int, time_text.split(":"))
    return hour * 60 + minute


def _in_range(period, current_minutes):
    try:
        start = _to_minutes(period[0])
        end = _to_minutes(period[1])
    except ValueError:
        return False

    return start <= current_minutes < end


def get_opening_status(opening_hours, now=None):
    """
    根據景點 opening_hours 判斷目前營業狀態。

    支援：
    - 09:00-17:00
    - 08:00-12:00、13:00-17:00
    - 週二公休
    - 全天開放
    - 24小時
    - 全天可通行
    - 平日 / 假日不同營業時間
    - 室內 / 戶外不同營業時間
    - 未公布固定開放時間
    """

    if not opening_hours:
        return "⚪ 營業時間未提供"

    now = now or datetime.now(TAIWAN_TZ)
    text = str(opening_hours).strip()

    # 沒有固定營業時間
    if "未公布固定開放時間" in text:
        return "⚪ 營業狀態待確認"

    # 判斷當天是否公休
    weekday_name = WEEKDAY_NAMES[now.weekday()]

    closed_patterns = (
        f"週{weekday_name}公休",
        f"星期{weekday_name}公休",
        f"週{weekday_name}休息",
        f"星期{weekday_name}休息",
    )

    if any(pattern in text for pattern in closed_patterns):
        return "🔴 今日公休"

    # 全天開放類型
    if (
        "全天開放" in text
        or "24小時" in text
        or "全天可通行" in text
    ):
        return "🟢 目前開放"

    # 統一不同的破折號格式
    normalized = (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("～", "-")
        .replace("~", "-")
    )

    current_minutes = now.hour * 60 + now.minute

    # 室內、戶外時段不同（例如角板山行館）
    indoor_match = re.search(r"室內\s*" + TIME_RANGE, normalized)
    outdoor_match = re.search(r"戶外\s*" + TIME_RANGE, normalized)

    if indoor_match and outdoor_match:
        indoor_open = _in_range(indoor_match.groups(), current_minutes)
        outdoor_open = _in_range(outdoor_match.groups(), current_minutes)

        if indoor_open and outdoor_open:
            return "🟢 營業中"
        if outdoor_open:
            return "🟡 戶外開放中，室內已休館"
        if indoor_open:
            return "🟡 室內開放中，戶外已休館"
        return "🔴 目前休息"

    periods = []

    # 平日 / 假日不同時間
    if now.weekday() < 5:
        weekday_match = re.search(
            r"平日\s*" + TIME_RANGE,
            normalized
        )

        if weekday_match:
            periods.append(weekday_match.groups())

    else:
        holiday_match = re.search(
            r"假日\s*" + TIME_RANGE,
            normalized
        )

        if holiday_match:
            periods.append(holiday_match.groups())

    # 如果沒有平日 / 假日格式，就抓全部時間區段
    if not periods:
        periods = re.findall(TIME_RANGE, normalized)

    # 找不到時間格式
    if not periods:
        return "⚪ 營業狀態待確認"

    # 檢查是否落在任一營業區段
    for period in periods:
        if _in_range(period, current_minutes):
            return "🟢 營業中"

    return "🔴 目前休息"