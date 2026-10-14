import json
import os
import unittest
from unittest.mock import MagicMock, patch

from modules.ai_service import gemini_reply as gemini
from handlers.message_handler import (
    get_itinerary_message,
    parse_stop_number,
)


ATTRACTIONS = [
    {
        "id": 1,
        "name": "測試景點甲",
        "category": "測試",
        "description": "測試介紹",
    },
    {
        "id": 2,
        "name": "測試景點乙",
        "category": "測試",
        "description": "測試介紹",
    },
]

CONTEXT = {"status": "available", "items": ATTRACTIONS}


def stop(identity):
    return {
        "kind": "attraction",
        "id": str(identity),
        "time": "上午",
        "note": "測試安排",
    }


class ItineraryCardTests(unittest.TestCase):
    def setUp(self):
        self.session = "test-itinerary-cards"
        gemini.clear_session(self.session)
        self.addCleanup(gemini.clear_session, self.session)

    def ask(self, data):
        raw = json.dumps(data, ensure_ascii=False)
        provider_response = {
            "candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": raw}]},
            }]
        }
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            json.dumps(provider_response).encode("utf-8")
        )

        with patch.dict(
            os.environ,
            {
                "GEMINI_ENABLED": "true",
                "GEMINI_API_KEY": "offline-test-key",
                "GEMINI_MODEL": "gemini-3.8-flash",
            },
        ), patch.object(
            gemini, "build_context", return_value={}
        ), patch.object(
            gemini, "load_attraction_context", return_value=CONTEXT
        ), patch.object(
            gemini, "event_context", return_value={}
        ), patch.object(
            gemini, "urlopen", return_value=response
        ):
            return gemini.get_gemini_reply(
                "幫我排行程", session_id=self.session
            )

    def card(self, text, session=None):
        with patch(
            "modules.attraction.attraction_service.get_all_attractions",
            return_value=ATTRACTIONS,
        ):
            return get_itinerary_message(
                text,
                self.session if session is None else session,
            )

    def test_second_station_matches_visible_order(self):
        reply = self.ask({
            "message": "行程草案",
            "stops": [stop(2), stop(1)],
        })

        self.assertIn("第2站｜上午｜測試景點甲", reply)
        card = self.card("看第二站")
        self.assertEqual(type(card).__name__, "FlexMessage")
        self.assertIn("測試景點甲", card.alt_text)

    def test_modification_replaces_mapping(self):
        self.ask({"message": "原行程", "stops": [stop(1), stop(2)]})
        self.ask({"message": "修改後", "stops": [stop(2), stop(1)]})

        self.assertIn("測試景點甲", self.card("看第2站").alt_text)

    def test_invalid_id_does_not_replace_previous_plan(self):
        self.ask({"message": "原行程", "stops": [stop(1)]})
        reply = self.ask({"message": "錯誤", "stops": [stop(999)]})

        self.assertEqual(reply, gemini.FORMAT_ERROR)
        self.assertEqual(
            gemini.get_saved_stops(self.session)[0]["id"], "1"
        )

    def test_other_stop_does_not_return_attraction_card(self):
        self.ask({
            "message": "行程",
            "stops": [
                stop(1),
                {
                    "kind": "other",
                    "name": "午餐安排",
                    "time": "中午",
                    "note": "先保留用餐時間",
                },
            ],
        })

        card = self.card("看第2站")
        self.assertEqual(type(card).__name__, "TextMessage")
        self.assertIn("午餐安排", card.text)

    def test_clear_and_separate_sessions(self):
        self.ask({"message": "行程", "stops": [stop(1)]})

        self.assertIn(
            "沒有可查看",
            self.card("看第一站", session="another-user").text,
        )

        gemini.clear_session(self.session)
        self.assertIn("沒有可查看", self.card("看第一站").text)

    def test_expiry_removes_mapping(self):
        self.ask({"message": "行程", "stops": [stop(1)]})

        with patch.object(
            gemini.time,
            "monotonic",
            return_value=gemini.time.monotonic() + gemini.TTL + 1,
        ):
            self.assertEqual(gemini.get_saved_stops(self.session), [])

    def test_out_of_range(self):
        self.ask({"message": "行程", "stops": [stop(1)]})
        self.assertIn("共有1站", self.card("看第9站").text)

    def test_edit_and_emergency_are_not_card_commands(self):
        self.assertEqual(parse_stop_number("看第二站"), 2)
        self.assertEqual(parse_stop_number("第2站的地圖"), 2)
        self.assertIsNone(parse_stop_number("第二站換掉"))
        self.assertIsNone(parse_stop_number("第二站有人受傷需要救護車"))


if __name__ == "__main__":
    unittest.main()