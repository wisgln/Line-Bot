import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.ai_service import get_reply
from modules.ai_service.local_products import load_products, get_local_products_reply


class LocalProductsTests(unittest.TestCase):
    def test_grouped_browse_and_new_topics(self):
        reply = get_reply('復興有什麼農特產？')
        for group in ('果香小旅行', '山野餐桌', '茶香與咖啡', '花草小日子', '農產變身伴手禮'):
            self.assertIn(group, reply)
        self.assertNotIn('已收錄', reply)
        self.assertLess(len(reply.encode('utf-16-le')) // 2, 5000)

    def test_processed_product_does_not_return_fresh_fruit(self):
        for question in ('水蜜桃米乖乖', '水蜜桃甘糀', '水蜜桃加工品'):
            reply = get_reply(question)
            self.assertIn('山裡好物｜水蜜桃加工伴手禮', reply)
            self.assertIn('沒有固定鮮果產季', reply)

    def test_catalog(self):
        entries = load_products()
        self.assertEqual(len(entries), 12)
        for question in ('復興有什麼農特產？', '想買伴手禮', '農產品'):
            reply = get_reply(question)
            for item in entries:
                self.assertIn(item['name'], reply)

    def test_details_and_purchase_context(self):
        for item in load_products():
            with self.subTest(name=item['name']):
                reply = get_reply(item['name'] + '哪裡買？')
                for value in (item['season'], item['source_url'], item['purchase_url'], '不代表今天有現貨'):
                    self.assertIn(value, reply)
                self.assertLess(len(reply.encode('utf-16-le')) // 2, 5000)

    def test_food_phrase_can_query_product(self):
        self.assertIn('產季', get_reply('想吃水蜜桃'))

    def test_ambiguous_products_and_unknown_product(self):
        reply = get_reply('水蜜桃和甜柿')
        self.assertIn('水蜜桃', reply)
        self.assertIn('甜柿', reply)
        self.assertIn('探索在地好物的起點', get_reply('榴槤農產品'))

    def test_nearby_does_not_claim_distance(self):
        self.assertIn('不能視為最近', get_reply('附近哪裡買甜柿'))

    def test_emergency_and_traffic_keep_priority(self):
        with patch('modules.ai_service.ai_service.get_local_products_reply') as products:
            self.assertIn('119', get_reply('買水蜜桃時有人受傷，需要救護車'))
            get_reply('買水蜜桃要搭什麼車')
            products.assert_not_called()

    def test_named_restaurant_keeps_priority(self):
        self.assertIn('用餐地址', get_reply('春梅餐飲店'))
        self.assertIsNone(get_local_products_reply('你好'))

    def test_bad_data_returns_friendly_reply(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'products.json'
            for text in ('{', '{}', '[]', '[{}]'):
                path.write_text(text, encoding='utf-8')
                with self.assertLogs('modules.ai_service.local_products', level='ERROR'):
                    self.assertIn('暫時', get_local_products_reply('水蜜桃', data_path=path))
            with self.assertLogs('modules.ai_service.local_products', level='ERROR'):
                self.assertIn('暫時', get_local_products_reply('水蜜桃', data_path=Path(folder)/'missing'))

    def test_duplicate_ids_and_invalid_url_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'products.json'
            entry = load_products()[0]
            for data in ([entry, entry], [dict(entry, source_url='http://example.com')]):
                path.write_text(json.dumps(data), encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_products(path)

    def test_input_validation(self):
        with self.assertRaises(TypeError):
            get_local_products_reply(None)
        self.assertIn('問題太長', get_local_products_reply('水蜜桃' * 1000))


if __name__ == '__main__':
    unittest.main()
