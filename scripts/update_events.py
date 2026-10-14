"""Download the complete official calendar; atomically replace only auto data."""
import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

API = "https://travel.tycg.gov.tw/open-api/zh-tw/Event/Calendar"
ROOT = Path(__file__).resolve().parents[1]


def fetch(url):
    with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=30) as response:
        raw = response.read(4000001)
    if len(raw) > 4000000:
        raise ValueError("Response too large")
    return json.loads(raw)


def calendar(year, fetcher=fetch):
    result = []
    seen = set()
    total = None
    for page in range(1, 101):
        payload = fetcher(f"{API}?year={year}&page={page}")
        info = payload["Infos"]
        count = int(info["Declaration"]["Total"])
        if count < 0 or (total is not None and count != total):
            raise ValueError("Calendar changed during download; retry later")
        total = count
        rows = info["Info"]
        if rows is None and total == 0:
            rows = []
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            raise ValueError("Invalid calendar rows")
        for row in rows:
            identity = str(row["Id"])
            if identity in seen:
                raise ValueError("Repeated page or duplicate id")
            seen.add(identity)
            result.append(row)
        if len(result) == total:
            return result
        if not rows or len(result) > total:
            raise ValueError("Incomplete calendar")
    raise ValueError("Too many calendar pages")


def convert(rows, today):
    result = {}
    for row in rows:
        name = row["Name"]
        if not isinstance(name, str):
            raise ValueError("Invalid title")
        # Conservative title filter: do not mistake a passing mention or 復興路 for a venue.
        if not any(word in name for word in ("復興區", "角板山", "小烏來", "拉拉山", "宇內溪", "雪霧鬧")):
            continue
        if str(row["Pending"]).lower() == "true":
            continue
        start = datetime.strptime(row["Start"], "%Y/%m/%d %H:%M:%S").date()
        end = datetime.strptime(row["End"], "%Y/%m/%d %H:%M:%S").date()
        if end < start:
            raise ValueError("Invalid event dates")
        if end < today:
            continue
        url = row["TYWebsite"]
        if url.startswith("travel.tycg.gov.tw/"):
            url = "https://" + url
        if not re.fullmatch(r"https://travel\.tycg\.gov\.tw/zh-tw/event/calendardetail/\d+", url):
            raise ValueError("Unexpected official URL")
        identity = "tycg-" + str(row["Id"])
        result[identity] = {
            "id": identity, "name": name,
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "location": "活動場地請查看官方詳情",
            "description": "🎉 官方行事曆新消息！點開詳情，看看活動內容與參加方式。",
            "schedule_note": "公告區間不代表每日舉辦；場次、地點及報名狀態請確認官方說明。",
            "source_url": url, "checked_on": today.isoformat(),
        }
    return sorted(result.values(), key=lambda e: (e["start_date"], e["id"]))


def update(destination=None, *, fetcher=fetch, today=None):
    today = today or datetime.now(timezone(timedelta(hours=8))).date()
    destination = Path(destination) if destination else ROOT / "data/events_auto.json"
    # Include the coming year, including cross-year announcements.
    rows = calendar(today.year, fetcher) + calendar(today.year + 1, fetcher)
    entries = convert(rows, today)
    raw = json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
    if len(raw.encode("utf-8")) > 200000:
        raise ValueError("Output too large")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                         delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
        os.replace(temporary, destination)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return len(entries)


if __name__ == "__main__":
    print(f"Official calendar updated: {update()} upcoming matching events")
