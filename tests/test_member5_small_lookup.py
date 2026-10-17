import copy
import json
import time
import unittest
from unittest.mock import patch
from modules.ai_service import get_reply
from modules.ai_service import gemini_reply as core
from modules.ai_service.query_context import small_context
from modules.merchant.merchant_cards import create_merchant_bubble

class SmallLookupTests(unittest.TestCase):
    def setUp(self):
        core._sessions.clear()
        core._plans.clear()

    def test_hours_bypasses_ai_in_session(self):
        core._sessions['test'] = (time.monotonic(), [{'role': 'user', 'parts': [{'text': '行程'}]}])
        with patch.object(core, 'get_gemini_reply', side_effect=AssertionError('AI called')):
            answer = get_reply('小烏來天空步道幾點關門？', session_id='test')
        self.assertIn('17:00', answer)

    def test_unknown_hours_does_not_guess(self):
        with patch.object(core, 'get_gemini_reply', side_effect=AssertionError('AI called')):
            answer = get_reply('不存在景點幾點關門？')
        self.assertIn('完整名稱', answer)

    def test_new_candidate_cap(self):
        context = {'attractions': {'items': [{'id': str(i), 'name': str(i)} for i in range(8)]}, 'merchants.json': [{'name': 'm'+str(i)} for i in range(8)], 'current_plan': []}
        result = small_context(context, '排行程')
        self.assertEqual(len(result['attractions']['items']) + len(result['merchants.json']), 5)
        self.assertEqual(len(context['attractions']['items']), 8)

    def test_pinned_preserved(self):
        context = {'attractions': {'items': [{'id': str(i), 'name': str(i)} for i in range(8)]}, 'merchants.json': [], 'current_plan': [{'kind': 'attraction', 'id': '7', 'name': '7'}]}
        result = small_context(context, '修改行程')
        self.assertIn('7', [x['id'] for x in result['attractions']['items']])
        self.assertEqual(len(result['attractions']['items']), 6)

    def test_unrelated_data_removed(self):
        result = small_context({'events': {}, 'faq.json': [], 'local_products.json': []}, '景點介紹')
        self.assertNotIn('events', result)
        self.assertNotIn('faq.json', result)
        self.assertNotIn('local_products.json', result)

    def test_map_fallback(self):
        card = create_merchant_bubble({'name': '測試店', 'address': '測試地址', 'category': '餐廳'})
        buttons = card['footer']['contents']
        maps = [b for b in buttons if b['action']['label'] == '📍 Google Maps']
        self.assertEqual(len(maps), 1)
        self.assertTrue(maps[0]['action']['uri'].startswith('https://www.google.com/maps/search/'))

if __name__ == '__main__':
    unittest.main()
