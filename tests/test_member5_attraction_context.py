import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from modules.ai_service.attraction_context import load_attraction_context
from modules.ai_service import gemini_reply as g


class AttractionContextTests(unittest.TestCase):
    def test_shared_data(self):
        context = load_attraction_context()
        self.assertEqual(context['status'], 'available')
        self.assertTrue(context['items'])
        for item in context['items']:
            self.assertIn('verification_note', item)

    def test_missing_and_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'attractions.json'
            self.assertEqual(load_attraction_context(path)['status'], 'missing')
            for text in ('{', '{}', '[null]'):
                path.write_text(text, encoding='utf-8')
                self.assertEqual(load_attraction_context(path)['status'], 'invalid')

    def test_blank_unknown_and_refresh(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'attractions.json'
            item = {'name': '測試景點', 'opening_hours': '', 'private_field': 'exclude'}
            path.write_text(json.dumps([item]), encoding='utf-8')
            first = load_attraction_context(path)['items'][0]
            self.assertIn('opening_hours', first['missing_information'])
            self.assertNotIn('private_field', first)
            item['opening_hours'] = '測試時間'
            path.write_text(json.dumps([item]), encoding='utf-8')
            self.assertEqual(load_attraction_context(path)['items'][0]['opening_hours'], '測試時間')

    def test_sent_to_gemini(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":"ok"}]}}]}'
        with patch.dict('os.environ', {'GEMINI_ENABLED':'true','GEMINI_API_KEY':'fake'}), patch.object(g, 'build_context', return_value={}), patch.object(g, 'urlopen', return_value=response) as call:
            g.get_gemini_reply('安排一日行程')
            body = json.loads(call.call_args.args[0].data)
            self.assertIn('小烏來天空步道', body['systemInstruction']['parts'][0]['text'])
