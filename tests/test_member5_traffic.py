import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.ai_service import get_reply
from modules.ai_service.traffic import (
    BUS_URL,
    ROAD_URL,
    get_traffic_reply,
    load_traffic,
)


class TrafficTests(unittest.TestCase):
    def test_jiaobanshan(self):
        reply = get_traffic_reply("怎麼去角板山")
        self.assertIn("【角板山】", reply)
        self.assertIn("502", reply)
        self.assertIn("假日", reply)
        self.assertIn(BUS_URL, reply)

    def test_lalashan(self):
        reply = get_traffic_reply("拉拉山公車")
        self.assertIn("【拉拉山】", reply)
        self.assertIn("林班口", reply)
        self.assertIn("回程", reply)

    def test_non_traffic_returns_none(self):
        for text in (
            "推薦餐廳",
            "拉拉山天氣",
            "需要下載 App 嗎",
        ):
            with self.subTest(text=text):
                self.assertIsNone(get_traffic_reply(text))

    def test_unknown_destination(self):
        reply = get_traffic_reply("怎麼去未知景點")
        self.assertIn("未提供專屬路線", reply)
        self.assertNotIn("【角板山】", reply)

    def test_multiple_places_are_not_transfer_plan(self):
        reply = get_traffic_reply("角板山到拉拉山怎麼搭車")
        self.assertIn("不是這些地點之間的轉乘規劃", reply)
        self.assertIn("【角板山】", reply)
        self.assertIn("【拉拉山】", reply)

    def test_road_question_provides_official_lookup(self):
        reply = get_traffic_reply("現在拉拉山封路了嗎")
        self.assertIn("管制公告", reply)
        self.assertIn(ROAD_URL, reply)
        self.assertNotIn("【拉拉山】", reply)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "missing.json"

            with self.assertLogs(
                "modules.ai_service.traffic",
                level="ERROR",
            ):
                reply = get_traffic_reply(
                    "角板山公車",
                    data_path=path,
                )

            self.assertIn("暫時無法讀取", reply)
            self.assertIn(BUS_URL, reply)

    def test_invalid_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "traffic.json"

            for content in (
                "{",
                "{}",
                "[]",
                '[{"id":"a"}]',
            ):
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")

                    with self.assertRaises(ValueError):
                        load_traffic(path)

    def test_duplicate_ids(self):
        item = load_traffic()[0]

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "traffic.json"
            path.write_text(
                json.dumps(
                    [item, item],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_traffic(path)

    def test_entry_point(self):
        reply = get_reply("怎麼去小烏來")
        self.assertIn("【小烏來】", reply)
        self.assertIn("502", reply)

    def test_emergency_has_priority(self):
        with patch(
            "modules.ai_service.ai_service.get_traffic_reply"
        ) as mock_traffic:
            reply = get_reply("公車上有人昏倒需要救護車")
            self.assertIn("119", reply)
            mock_traffic.assert_not_called()

    def test_road_question_has_priority_over_weather(self):
        with patch(
            "modules.weather.weather_service.get_weather_reply"
        ) as mock_weather:
            reply = get_reply("下雨封路了嗎")
            self.assertIn(ROAD_URL, reply)
            mock_weather.assert_not_called()


if __name__ == "__main__":
    unittest.main()