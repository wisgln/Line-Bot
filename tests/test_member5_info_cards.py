import json
import unittest
from types import SimpleNamespace as S
from unittest.mock import patch
from linebot.v3.messaging import FlexMessage, TextMessage
from modules.ai_service import info_cards as cards
from handlers import message_handler as handler

FORECAST = "桃園市復興區｜近期天氣預報\n\n10/25 12:00～10/25 18:00\n多雲。氣溫 20 至 25 度。\n\n10/25 18:00～10/26 00:00\n短暫雨。\n\n查詢時間：10/25 13:00（台灣時間）\n資料來源：中央氣象署；以上為預報，非即時觀測。"


class InfoCardTests(unittest.TestCase):
    def test_emergency_phone_buttons_and_disclaimer(self):
        msg = cards.get_info_card("救命，需要救護車，還想查天氣")
        self.assertIsInstance(msg, FlexMessage)
        for value in ("tel:119", "tel:110", "tel:165", "未通知救援單位"):
            self.assertIn(value, json.dumps(msg.to_dict(), ensure_ascii=False))

    def test_emergency_data_failure_keeps_phones(self):
        with patch.object(cards, "load_emergency_contacts", side_effect=ValueError):
            msg = cards.get_info_card("緊急聯絡")
        self.assertIsInstance(msg, TextMessage)
        self.assertIn("119", msg.text)

    def test_weather_periods_and_refresh(self):
        with patch("modules.weather.weather_service.get_weather_reply", return_value=FORECAST) as fetch:
            msg = cards.get_info_card("復興區天氣")
        fetch.assert_called_once()
        data = json.loads(json.dumps(msg.to_dict(), ensure_ascii=False))["contents"]
        self.assertEqual(len(data["contents"]), 2)
        self.assertIn("20 至 25", json.dumps(data["contents"][0], ensure_ascii=False))
        self.assertNotIn("20 至 25", json.dumps(data["contents"][1], ensure_ascii=False))
        self.assertIn("更新天氣", json.dumps(msg.to_dict(), ensure_ascii=False))

    def test_weather_failure_hides_technical_errors(self):
        with patch("modules.weather.weather_service.get_weather_reply", return_value="尚未設定 WEATHER_API_KEY"):
            msg = cards.get_info_card("天氣")
        self.assertIsInstance(msg, FlexMessage)
        self.assertNotIn("WEATHER_API_KEY", json.dumps(msg.to_dict(), ensure_ascii=False))
        self.assertIn("重新查詢", json.dumps(msg.to_dict(), ensure_ascii=False))

    def test_all_product_details_have_sources(self):
        for item in cards.load_products():
            with self.subTest(item=item["name"]):
                msg = cards.get_info_card("農產介紹：" + item["name"])
                self.assertIsInstance(msg, FlexMessage)
                self.assertIn(item["season"], json.dumps(msg.to_dict(), ensure_ascii=False))
                self.assertIn("不代表目前有現貨", json.dumps(msg.to_dict(), ensure_ascii=False))

    def test_product_menu_pagination(self):
        msg = cards.get_info_card("農特產")
        self.assertIn("農產介紹", json.dumps(msg.to_dict(), ensure_ascii=False))
        self.assertIn("下一頁", json.dumps(msg.to_dict(), ensure_ascii=False))
        msg = cards.get_info_card("農產列表：第2頁")
        self.assertIsInstance(msg, FlexMessage)
        self.assertIn("上一頁", json.dumps(msg.to_dict(), ensure_ascii=False))
        self.assertIsInstance(cards.get_info_card("農產列表：第999頁"), TextMessage)

    def test_plan_and_traffic_not_intercepted(self):
        for text in ("幫我排水蜜桃一日遊", "去買甜柿怎麼搭車"):
            self.assertIsNone(cards.get_info_card(text))
        with patch("modules.ai_service.gemini_reply.has_session", return_value=True):
            self.assertIsNone(cards.get_info_card("下雨，第二站換掉", "test"))

    def test_handler_sends_flex_without_ai(self):
        for text in ("天氣", "緊急聯絡", "農產品", "水蜜桃產季"):
            with self.subTest(text=text), patch.object(handler, "ApiClient"), \
                    patch.object(handler, "MessagingApi") as api, \
                    patch.object(handler, "get_ai_reply") as ai, \
                    patch("modules.weather.weather_service.get_weather_reply", return_value=FORECAST):
                handler.handle_text_message(S(message=S(text=text), source=S(user_id="offline"), reply_token="offline"), None)
                msg = api.return_value.reply_message.call_args.args[0].messages[0]
                self.assertIsInstance(msg, FlexMessage)
                ai.assert_not_called()
                api.return_value.reply_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
