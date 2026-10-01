import json
import os
from pathlib import Path
import tempfile
import unittest

from modules.ai_service import get_reply
from modules.ai_service.ai_service import FALLBACK, WELCOME
from modules.ai_service.faq import find_answer, load_faq
from modules.ai_service.intent import detect_intent


class FAQTests(unittest.TestCase):
    def test_all_questions(self):
        for entry in load_faq():
            with self.subTest(id=entry["id"]):
                self.assertEqual(get_reply(entry["question"]), entry["answer"])

    def test_normalization(self):
        self.assertIn("不需要另外下載", get_reply("請問需要下載 ＡＰＰ 嗎？"))

    def test_welcome(self):
        for text in ("", "  ", "AI 問答", "使用說明"):
            self.assertEqual(get_reply(text), WELCOME)

    def test_unknown(self):
        self.assertEqual(get_reply("幫我買股票"), FALLBACK)

    def test_pending_services(self):
        for question in ("明天會下雨嗎", "天空步道營業時間", "公車班次", "推薦餐廳"):
            self.assertIn("目前", get_reply(question))

    def test_missing_data(self):
        with self.assertLogs("modules.ai_service.ai_service", level="ERROR"):
            self.assertIn("暫時無法讀取", get_reply("下載app", faq_path="absent-faq.json"))

    def test_invalid_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "faq.json"
            for data in ("{", "{}", "[]", '[{"id": "a"}]'):
                path.write_text(data, encoding="utf-8")
                with self.assertLogs("modules.ai_service.ai_service", level="ERROR"):
                    self.assertIn("暫時無法讀取", get_reply("問題", faq_path=path))

    def test_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "faq.json"
            item = load_faq()[0]
            path.write_text(json.dumps([item, item]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_faq(path)

    def test_independent_of_working_directory(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                self.assertIn("不需要另外下載", get_reply("下載app"))
            finally:
                os.chdir(previous)

    def test_ambiguous_keywords(self):
        entries = [{"question": "Q1", "keywords": ["測試"], "answer": "A"},
                   {"question": "Q2", "keywords": ["測試"], "answer": "B"}]
        self.assertIsNone(find_answer("測試看看", entries))

    def test_specific_intent(self):
        self.assertEqual(detect_intent("景點營業時間"), "opening_hours")

    def test_long_input(self):
        self.assertIn("問題太長", get_reply("字" * 2001))

    def test_input_type(self):
        with self.assertRaises(TypeError):
            get_reply(None)


if __name__ == "__main__":
    unittest.main()
