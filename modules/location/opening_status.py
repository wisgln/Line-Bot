from datetime import datetime
import re


WEEKDAY_NAMES = {
    0: "一",
    1: "二",
    2: "三",
    3: "四",
    4: "五",
    5: "六",
    6: "日",
}


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
    - 未公布固定開放時間
    """

    if not opening_hours:
        return "⚪ 營業時間未提供"

    now = now or datetime.now()
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

    periods = []

    # 平日 / 假日不同時間
    if now.weekday() < 5:
        weekday_match = re.search(
            r"平日\s*(\d{1,2}:\d{2})-(\d{1,2}:\d{2})",
            normalized
        )

        if weekday_match:
            periods.append(weekday_match.groups())

    else:
        holiday_match = re.search(
            r"假日\s*(\d{1,2}:\d{2})-(\d{1,2}:\d{2})",
            normalized
        )

        if holiday_match:
            periods.append(holiday_match.groups())

    # 如果沒有平日 / 假日格式，就抓全部時間區段
    if not periods:
        periods = re.findall(
            r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})",
            normalized
        )

    # 找不到時間格式
    if not periods:
        return "⚪ 營業狀態待確認"

    current_minutes = now.hour * 60 + now.minute

    # 檢查是否落在任一營業區段
    for start_text, end_text in periods:
        try:
            start_hour, start_minute = map(
                int,
                start_text.split(":")
            )

            end_hour, end_minute = map(
                int,
                end_text.split(":")
            )

            start = start_hour * 60 + start_minute
            end = end_hour * 60 + end_minute

            if start <= current_minutes < end:
                return "🟢 營業中"

        except ValueError:
            continue

    return "🔴 目前休息"