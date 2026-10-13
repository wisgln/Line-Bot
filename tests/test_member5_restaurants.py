import unittest

from modules.ai_service import get_reply
from modules.merchant.merchant_service import load_merchants, format_merchant


class RestaurantTests(unittest.TestCase):
    def test_all_twenty_visible(self):
        restaurants = [m for m in load_merchants() if m['category'] == '餐廳']
        self.assertEqual(len(restaurants), 20)
        for question in ('餐廳', '推薦餐廳', '美食', '推薦美食', '肚子餓了，有什麼能吃？'):
            with self.subTest(question=question):
                reply = get_reply(question)
                for merchant in restaurants:
                    self.assertIn(merchant['name'], reply)
                self.assertLess(len(reply.encode('utf-16-le')) // 2, 5000)

    def test_every_restaurant_returns_details_and_price_context(self):
        for merchant in load_merchants():
            if merchant['category'] != '餐廳':
                continue
            with self.subTest(name=merchant['name']):
                reply = get_reply(merchant['name'])
                self.assertIn(merchant['address'], reply)
                self.assertIn(merchant['price_note'], reply)
                self.assertIn(merchant['source_url'], reply)
                self.assertIn('🌿', reply)
                self.assertLess(len(reply.encode('utf-16-le')) // 2, 5000)

    def test_overlapping_names_choose_exact_shop(self):
        self.assertIn('中正路138號之1', get_reply('源元發飲食店'))
        self.assertIn('中山路13之1號', get_reply('元發飲食店'))

    def test_budget_and_group_conditions_remain_explicit(self):
        reply = get_reply('瑞士鄉村農莊')
        self.assertIn('350～600 元／人', reply)
        self.assertIn('並非單道菜售價', reply)
        self.assertIn('官方旅遊資訊', reply)
        reply = get_reply('比雅山景觀咖啡座')
        self.assertIn('20 人以上', reply)
        self.assertIn('10 人以上', reply)
        self.assertIn('非一般散客簡餐價格', reply)

    def test_missing_price_not_shown_as_zero(self):
        reply = format_merchant(dict(name='測試', category='餐廳', address='復興區'))
        self.assertIn('未收錄', reply)
        self.assertNotIn('0 元', reply)


if __name__ == '__main__':
    unittest.main()
