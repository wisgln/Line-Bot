"""Adapt shared attraction data without changing the location team's schema."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ('id', 'name', 'category', 'latitude', 'longitude', 'address',
          'description', 'maps_url', 'opening_hours', 'phone', 'source_url',
          'source_checked_on', 'accessibility', 'parking', 'walking_notes',
          'suggested_duration')


def load_attraction_context(path=None):
    path = Path(path) if path is not None else ROOT / 'data' / 'attractions.json'
    try:
        if path.stat().st_size > 200_000:
            raise ValueError('Attraction data too large')
        with path.open(encoding='utf-8-sig') as stream:
            entries = json.load(stream)
        if not isinstance(entries, list):
            raise ValueError('Expected attraction list')
        result = []
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get('name'), str) or not entry['name'].strip():
                raise ValueError('Invalid attraction')
            item = {key: entry[key] for key in FIELDS if key in entry and entry[key] not in ('', None)}
            item['missing_information'] = [key for key in ('opening_hours', 'source_url', 'source_checked_on', 'accessibility', 'parking', 'walking_notes', 'suggested_duration') if key not in item]
            item['verification_note'] = '專案提供的參考資料，未由本程式獨立查核；來源日期不代表即時有效。'
            result.append(item)
        return {'status': 'available', 'items': result}
    except FileNotFoundError:
        return {'status': 'missing', 'items': []}
    except (OSError, ValueError):
        return {'status': 'invalid', 'items': []}
