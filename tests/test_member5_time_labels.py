import unittest
from modules.ai_service.groq_reply import _prepare_stops, _validate
from modules.ai_service import gemini_reply as core

class TimeLabels(unittest.TestCase):
    def test_label(self):
        stops = [{'time': '上午第二站'}, {'time': '第2天下午第三站'}]
        result = _prepare_stops(stops, '', [])
        self.assertEqual([x['time'] for x in result], ['上午', '第2天下午'])
        self.assertEqual(stops[0]['time'], '上午第二站')

    def test_unknown_unchanged(self):
        self.assertEqual(_prepare_stops([{'time': '上午下午'}], '', [])[0]['time'], '上午下午')

    def test_total_and_lunch(self):
        stops = [{'kind': 'attraction', 'id': str(i)} for i in range(3)] + [{'kind': 'other', 'name': '午餐安排'}]
        result = _prepare_stops(stops, '兩個景點加午餐', [])
        self.assertEqual(len(result), 3)
        self.assertEqual(result[-1]['name'], '午餐安排')
        self.assertEqual(len(_prepare_stops(stops, '兩個景點', stops)), 4)

    def test_actual_validation(self):
        context = {'attractions': {'status': 'available', 'items': [{'id': 'a', 'name': '甲'}, {'id': 'b', 'name': '乙'}]}, 'current_plan': []}
        stops = [{'kind': 'attraction', 'id': 'a', 'time': '上午第一站', 'note': ''}, {'kind': 'attraction', 'id': 'b', 'time': '上午第二站', 'note': ''}, {'kind': 'other', 'name': '午餐安排', 'time': '中午', 'note': ''}]
        self.assertEqual(len(_validate(core, stops, context, '兩個景點加午餐')), 3)
