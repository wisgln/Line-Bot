from datetime import datetime, timezone, timedelta

from modules.location.opening_status import get_opening_status


TAIWAN_TZ = timezone(timedelta(hours=8))


def make_time(year, month, day, hour, minute=0):
    return datetime(
        year,
        month,
        day,
        hour,
        minute,
        tzinfo=TAIWAN_TZ,
    )


def test_24_hours_open():
    now = make_time(2026, 10, 19, 3, 0)

    assert get_opening_status(
        "24小時",
        now=now,
    ) == "🟢 目前開放"


def test_normal_opening_hours_open():
    now = make_time(2026, 10, 19, 10, 0)

    assert get_opening_status(
        "09:00-17:00",
        now=now,
    ) == "🟢 營業中"


def test_normal_opening_hours_closed():
    now = make_time(2026, 10, 19, 18, 0)

    assert get_opening_status(
        "09:00-17:00",
        now=now,
    ) == "🔴 目前休息"


def test_split_opening_hours():
    now = make_time(2026, 10, 19, 14, 0)

    assert get_opening_status(
        "08:00-12:00、13:00-17:00",
        now=now,
    ) == "🟢 營業中"


def test_split_opening_hours_break_time():
    now = make_time(2026, 10, 19, 12, 30)

    assert get_opening_status(
        "08:00-12:00、13:00-17:00",
        now=now,
    ) == "🔴 目前休息"


def test_weekday_closed():
    # 2026/10/20 是星期二
    now = make_time(2026, 10, 20, 10, 0)

    assert get_opening_status(
        "09:00-17:00；週二公休",
        now=now,
    ) == "🔴 今日公休"


def test_weekday_and_holiday_hours():
    # 2026/10/24 是星期六
    now = make_time(2026, 10, 24, 10, 30)

    assert get_opening_status(
        "平日 09:00-17:00；假日 10:00-18:00",
        now=now,
    ) == "🟢 營業中"


def test_unknown_opening_hours():
    now = make_time(2026, 10, 19, 10, 0)

    assert get_opening_status(
        "未公布固定開放時間",
        now=now,
    ) == "⚪ 營業狀態待確認"