import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from modules.ai_service import get_reply
from modules.ai_service.events import event_context, get_events_reply, load_events


class EventTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'events.json'
        self.entry = {'id':'test','name':'測試活動','location':'復興','description':'測試',
                      'schedule_note':'先確認場次','source_url':'https://travel.tycg.gov.tw/test',
                      'start_date':'2026-10-01','end_date':'2026-10-12','checked_on':'2026-10-10'}
        self.save()

    def save(self):
        self.path.write_text(json.dumps([self.entry]), encoding='utf-8')

    def test_end_date_inclusive(self):
        self.assertEqual(len(event_context(today=date(2026,10,12),path=self.path)['items']),1)
        self.assertEqual(event_context(today=date(2026,10,13),path=self.path)['items'],[])

    def test_stale_and_future_check_excluded(self):
        self.entry['end_date']='2027-01-01'
        for checked in ('2026-08-01','2026-10-20'):
            self.entry['checked_on']=checked
            self.save()
            self.assertEqual(event_context(today=date(2026,10,12),path=self.path)['items'],[])

    def test_tomorrow_excludes_ended(self):
        reply=get_events_reply('明天有活動嗎',today=date(2026,10,12),path=self.path)
        self.assertNotIn('✨ 測試活動',reply)
        self.assertIn('2026/10/13',reply)

    def test_weekend(self):
        reply=get_events_reply('週末活動',today=date(2026,10,12),path=self.path)
        self.assertIn('2026/10/17～2026/10/18',reply)

    def test_missing_file(self):
        self.path.unlink()
        self.assertIn('官方公告',get_events_reply('活動',path=self.path))

    def test_invalid_dates(self):
        self.entry['start_date']='2027-01-01'
        self.save()
        with self.assertRaises(ValueError): load_events(self.path)

    def test_non_event(self):
        self.assertIsNone(get_events_reply('推薦餐廳'))

    def test_routing_before_ai_and_emergency_first(self):
        with patch('modules.ai_service.ai_service.get_events_reply', return_value='活動回覆') as events, patch('modules.ai_service.gemini_reply.get_gemini_reply') as ai:
            self.assertEqual(get_reply('最近有哪些活動'), '活動回覆')
            ai.assert_not_called()
            events.reset_mock()
            self.assertIn('119', get_reply('活動現場有人昏倒需要救護車'))
            events.assert_not_called()
