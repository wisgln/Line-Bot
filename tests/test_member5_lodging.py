import unittest
from modules.ai_service import get_reply
from modules.merchant.merchant_service import load_merchants, format_merchant


class LodgingTests(unittest.TestCase):
    def test_all_twenty_visible_from_category_and_natural_question(self):
        lodgings = [m for m in load_merchants() if m['category'] == '民宿']
        self.assertEqual(len(lodgings), 20)
        for question in ('民宿', '住宿', '推薦民宿', '想在山上住一晚'):
            reply = get_reply(question)
            for merchant in lodgings:
                self.assertIn(merchant['name'], reply)
            self.assertLess(len(reply.encode('utf-16-le')) // 2, 5000)

    def test_every_lodging_name_returns_its_details(self):
        for merchant in load_merchants():
            if merchant['category'] == '民宿':
                with self.subTest(name=merchant['name']):
                    reply = get_reply(merchant['name'])
                    self.assertIn(merchant['address'], reply)
                    self.assertIn('🌿', reply)
                    self.assertIn('https://', reply)

    def test_no_maps_does_not_hide_source_or_crash(self):
        for category in ('餐廳', '民宿'):
            reply = format_merchant(dict(name='測試',category=category,address='復興區',source_url='https://example.com/'))
            self.assertIn('https://example.com/', reply)

    def test_tourism_source_not_labelled_operator_website(self):
        reply = get_reply('山是我家')
        self.assertIn('官方旅遊資訊', reply)
        self.assertNotIn('民宿官網', reply)
        self.assertIn('未收錄', reply)


if __name__ == '__main__':
    unittest.main()
