import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.ai_service import get_reply
from modules.ai_service.emergency import (
    FALLBACK_REPLY,
    get_emergency_reply,
    is_emergency_query,
    load_emergency_contacts,
)


class EmergencyTests(unittest.TestCase):
    def test_official_phone_mapping(self):
        contacts = load_emergency_contacts()
        self.assertEqual(
            {item["id"]: item["phone"] for item in contacts},
            {
                "fire_rescue": "119",
                "police": "110",
                "anti_fraud": "165",
            },
        )

    def test_emergency_questions(self):
        for text in (
            "緊急聯絡",
            "需要救護車",
            "山區迷路需要救援",
            "我要報警",
            "遇到詐騙",
            "１１９",
            "SOS",
        ):
            with self.subTest(text=text):
                self.assertTrue(is_emergency_query(text))

    def test_normal_questions_do_not_match(self):
        for text in (
            "推薦餐廳",
            "復興區天氣如何",
            "需要下載 App 嗎",
        ):
            with self.subTest(text=text):
                self.assertIsNone(get_emergency_reply(text))

    def test_reply_contains_contacts_and_limit(self):
        reply = get_emergency_reply("緊急聯絡")
        for expected in ("119", "110", "165", "不會代為報案"):
            self.assertIn(expected, reply)

    def test_missing_file_uses_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing.json"
            with self.assertLogs(
                "modules.ai_service.emergency",
                level="ERROR",
            ):
                reply = get_emergency_reply(
                    "緊急聯絡",
                    data_path=missing,
                )
            self.assertEqual(reply, FALLBACK_REPLY)

    def test_invalid_json_uses_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "emergency.json"
            path.write_text("{", encoding="utf-8")

            with self.assertLogs(
                "modules.ai_service.emergency",
                level="ERROR",
            ):
                reply = get_emergency_reply(
                    "救護車",
                    data_path=path,
                )
            self.assertEqual(reply, FALLBACK_REPLY)

    def test_wrong_phone_is_rejected(self):
        contacts = load_emergency_contacts()
        contacts[0]["phone"] = "123"

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "emergency.json"
            path.write_text(
                json.dumps(contacts, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_emergency_contacts(path)

    def test_missing_contact_is_rejected(self):
        contacts = load_emergency_contacts()[:-1]

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "emergency.json"
            path.write_text(
                json.dumps(contacts, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_emergency_contacts(path)

    def test_emergency_bypasses_faq_and_merchants(self):
        with patch(
            "modules.ai_service.ai_service.load_faq"
        ) as mock_faq, patch(
            "modules.merchant.merchant_service.load_merchants"
        ) as mock_merchants:
            reply = get_reply("泰雅小棧附近有人受傷，需要救護車")
            self.assertIn("119", reply)
            mock_faq.assert_not_called()
            mock_merchants.assert_not_called()

    def test_emergency_has_priority_over_weather(self):
        with patch(
            "modules.weather.weather_service.get_weather_reply"
        ) as mock_weather:
            reply = get_reply("下雨時山區有人受傷，需要救援")
            self.assertIn("119", reply)
            mock_weather.assert_not_called()


if __name__ == "__main__":
    unittest.main()