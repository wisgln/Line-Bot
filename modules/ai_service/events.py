"""Date-filtered local event references; no live availability claims."""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from .intent import normalize

DATA_PATH = Path(__file__).resolve().parents[2] / 'data' / 'events.json'
CALENDAR = 'https://travel.tycg.gov.tw/zh-tw/event/calendar/'
NEWS = 'https://www.fuxing.tycg.gov.tw/News.aspx?n=5708&sms=11057'
HOSTS = {'typass.tycg.gov.tw', 'travel.tycg.gov.tw', 'www.fuxing.tycg.gov.tw'}


def taiwan_today():
    return datetime.now(timezone(timedelta(hours=8))).date()


def load_events(path=None):
    path = Path(path) if path is not None else DATA_PATH
    if path.stat().st_size > 200000:
        raise ValueError('Event file too large')
    entries = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(entries, list):
        raise ValueError('Events must be a list')
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Invalid event')
        for field in ('id', 'name', 'location', 'description', 'schedule_note', 'source_url', 'start_date', 'end_date', 'checked_on'):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError('Missing event field')
        if entry['id'] in seen:
            raise ValueError('Duplicate event id')
        seen.add(entry['id'])
        if date.fromisoformat(entry['end_date']) < date.fromisoformat(entry['start_date']):
            raise ValueError('Invalid event range')
        date.fromisoformat(entry['checked_on'])
        url = urlparse(entry['source_url'])
        if url.scheme != 'https' or url.hostname not in HOSTS:
            raise ValueError('Invalid official source')
    return entries


def event_context(*, today=None, path=None, end=None):
    today = today or taiwan_today()
    end = end or today + timedelta(days=30)
    try:
        entries = load_events(path)
    except (OSError, ValueError):
        return {'status': 'unavailable', 'as_of': today.isoformat(), 'items': []}
    if path is None:
        try:
            automatic = load_events(DATA_PATH.with_name('events_auto.json'))
        except (OSError, ValueError):
            automatic = []
        known_urls = {e['source_url'] for e in entries}
        entries += [e for e in automatic if e['source_url'] not in known_urls]
    items = [e for e in entries if date.fromisoformat(e['end_date']) >= today
             and date.fromisoformat(e['start_date']) <= end
             and 0 <= (today - date.fromisoformat(e['checked_on'])).days <= 30]
    return {'status': 'reference_only', 'as_of': today.isoformat(), 'items': items,
            'notice': '公告期間有交集不代表指定日有場次；非即時查詢，需向主辦方確認。'}


def get_events_reply(text, *, today=None, path=None):
    query = normalize(text)
    if not any(word in query for word in ('活動', '市集', '祭典', '慶典', '復興漫遊', '拾光之旅')):
        return None
    today = today or taiwan_today()
    start, end = today, today + timedelta(days=30)
    label = '未來30天'
    if '下週末' in query or '下周末' in query:
        start = today + timedelta(days=12 - today.weekday())
        end, label = start + timedelta(days=1), '下週末'
    elif '今天' in query:
        end, label = today, '今天'
    elif '明天' in query:
        start = end = today + timedelta(days=1)
        label = '明天'
    elif '週末' in query or '周末' in query:
        start = today + timedelta(days=max(0, 5 - today.weekday()))
        end = start + timedelta(days=0 if today.weekday() == 6 else 1)
        label = '本週末'
    context = event_context(today=today, path=path, end=end)
    items = [e for e in context['items'] if date.fromisoformat(e['end_date']) >= start]
    lines = ['🎉 復興活動小幫手', f'📅 {label}｜{start:%Y/%m/%d}～{end:%Y/%m/%d}', '']
    if items:
        lines.append('以下公告期間涵蓋查詢日期，實際場次請先確認：')
        for entry in items[:3]:
            lines.extend(['', '✨ ' + entry['name'], '📍 ' + entry['location'],
                          '🗓 公告期間：' + entry['start_date'] + '～' + entry['end_date'],
                          entry['description'], '💡 ' + entry['schedule_note'],
                          '🔗 詳情與預約說明', entry['source_url'], '資料查閱：' + entry['checked_on']])
    else:
        lines.append('這段時間還沒有可提供的近期活動資料，不代表當地沒有活動。')
        if context['status'] == 'unavailable':
            lines.append('資料暫時無法讀取，可先查看下方官方公告。')
    lines.extend(['', '🔎 想找更多活動？', '桃園活動行事曆', CALENDAR, '復興區公所公告', NEWS,
                  '提醒：這是公告資料整理，異動及報名狀態以主辦方為準。'])
    return '\n'.join(lines)
