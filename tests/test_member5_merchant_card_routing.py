import unittest
from types import SimpleNamespace as S
from unittest.mock import patch

from handlers import message_handler as handler
from linebot.v3.messaging import FlexMessage, TextMessage
from modules.merchant import merchant_cards as cards


class MerchantCardRoutingTests(unittest.TestCase):
    def test_handler_replies_with_cards_without_ai(self):
        for question in ("餐廳", "民宿", "請推薦餐廳", "請幫我推薦民宿",
                         "瑞士鄉村農莊", "商家詳細：瑞士鄉村農莊"):
            with self.subTest(question=question), patch.object(handler, "ApiClient"), \
                    patch.object(handler, "MessagingApi") as api, \
                    patch.object(handler, "get_ai_reply") as ai:
                event = S(message=S(text=question), source=S(user_id="offline"), reply_token="offline")
                handler.handle_text_message(event, None)
                message = api.return_value.reply_message.call_args.args[0].messages[0]
                self.assertIsInstance(message, FlexMessage)
                ai.assert_not_called()

    def test_every_merchant_has_details_and_itinerary_card(self):
        for merchant in cards.load_merchants():
            with self.subTest(merchant=merchant["name"]):
                message = cards.get_merchant_message("商家詳細：" + merchant["name"])
                self.assertIsInstance(message, FlexMessage)
                self.assertIn("https://www.google.com/maps", message.to_json())
                stop = dict(id=merchant["id"], name=merchant["name"], kind="merchant", note="")
                with patch("modules.ai_service.gemini_reply.get_saved_stops", return_value=[stop]):
                    self.assertIsInstance(handler.get_itinerary_message("看第1站", "offline"), FlexMessage)

    def test_other_stop_is_not_assigned_a_store(self):
        stop = dict(id="", name="自備便當", kind="other", note="")
        with patch("modules.ai_service.gemini_reply.get_saved_stops", return_value=[stop]):
            self.assertIsInstance(handler.get_itinerary_message("看第1站", "offline"), TextMessage)

    def test_general_questions_are_not_captured_by_menu(self):
        for question in ("請推薦餐廳並排兩天行程", "幫我安排一日遊", "附近有哪些民宿"):
            self.assertIsNone(cards.get_merchant_message(question))

    def test_stale_id_does_not_open_another_store(self):
        merchant = cards.load_merchants()[0]
        stop = dict(id="missing-id", name=merchant["name"], kind="merchant", note="")
        with patch("modules.ai_service.gemini_reply.get_saved_stops", return_value=[stop]):
            self.assertIsInstance(handler.get_itinerary_message("看第1站", "offline"), TextMessage)


if __name__ == "__main__":
    unittest.main()
