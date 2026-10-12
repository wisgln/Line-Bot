import unittest
from unittest.mock import patch

from modules.ai_service import get_reply
from modules.ai_service.ai_service import FALLBACK, NEARBY_REPLY
from modules.ai_service.intent import detect_intent


class NaturalLanguageTests(unittest.TestCase):
    def test_food_intent(self):
        for text in (
            "肚子餓了，有什麼能吃？",
            "晚餐吃什麼",
            "想吃在地小吃",
        ):
            with self.subTest(text=text):
                self.assertEqual(detect_intent(text), "merchant")

    def test_lodging_intent(self):
        for text in (
            "想在山上住一晚",
            "哪裡可以過夜",
            "想找房間",
        ):
            with self.subTest(text=text):
                self.assertEqual(detect_intent(text), "lodging")

    def test_food_routes_to_restaurants(self):
        with patch(
            "modules.merchant.merchant_service.load_merchants",
            return_value=[],
        ), patch(
            "modules.merchant.merchant_service.get_merchant_reply",
            return_value="模擬餐廳清單",
        ) as mock_reply:
            self.assertEqual(
                get_reply("肚子餓了，有什麼能吃？"),
                "模擬餐廳清單",
            )
            mock_reply.assert_called_once_with("餐廳")

    def test_lodging_routes_to_lodging(self):
        with patch(
            "modules.merchant.merchant_service.load_merchants",
            return_value=[],
        ), patch(
            "modules.merchant.merchant_service.get_merchant_reply",
            return_value="模擬住宿資訊",
        ) as mock_reply:
            self.assertEqual(
                get_reply("想在山上住一晚"),
                "模擬住宿資訊",
            )
            mock_reply.assert_called_once_with("民宿")

    def test_new_traffic_phrase_preserves_destination(self):
        reply = get_reply("我要去拉拉山，要搭什麼車？")
        self.assertIn("【拉拉山】", reply)

    def test_nearby_does_not_return_all_merchants(self):
        with patch(
            "modules.merchant.merchant_service.get_merchant_reply"
        ) as mock_reply:
            self.assertEqual(
                get_reply("附近有什麼吃的？"),
                NEARBY_REPLY,
            )
            mock_reply.assert_not_called()

    def test_named_merchant_coupon_is_not_shop_details(self):
        with patch(
            "modules.merchant.merchant_service.get_merchant_reply"
        ) as mock_reply:
            reply = get_reply("泰雅小棧特色料理有優惠券嗎")
            self.assertIn("尚未提供優惠券", reply)
            mock_reply.assert_not_called()

    def test_emergency_still_has_priority(self):
        with patch(
            "modules.ai_service.ai_service.get_traffic_reply"
        ) as mock_traffic:
            reply = get_reply("搭車時有人昏倒，需要救護車")
            self.assertIn("119", reply)
            mock_traffic.assert_not_called()

    def test_unknown_question(self):
        self.assertEqual(get_reply("幫我買股票"), FALLBACK)


if __name__ == "__main__":
    unittest.main()