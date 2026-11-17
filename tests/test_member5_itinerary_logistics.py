import unittest
import time
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from modules.ai_service.groq_reply import (
    _ensure_overnight_basics,
    _normalize_unknown_arrangements,
    _plan_traffic_reply,
    get_groq_reply,
)
from modules.ai_service import gemini_reply as core
from modules.ai_service.query_context import small_context


class ItineraryLogisticsTests(unittest.TestCase):
    def tearDown(self):
        core._sessions.clear()
        core._plans.clear()

    def test_overnight_plan_adds_meals_and_lodging_without_questions(self):
        context = {
            "merchants.json": [
                {"name": "山景餐廳", "category": "餐廳"},
                {"name": "溪谷餐廳", "category": "餐廳"},
                {"name": "森林民宿", "category": "民宿"},
            ]
        }
        stops = [
            {"kind": "attraction", "id": "1", "time": "第1天上午", "note": ""},
            {"kind": "attraction", "id": "2", "time": "第1天下午", "note": ""},
            {"kind": "attraction", "id": "3", "time": "第2天上午", "note": ""},
        ]

        result = _ensure_overnight_basics(stops, "安排兩天一夜", context)
        names = [stop.get("name") for stop in result]

        self.assertIn("山景餐廳", names)
        self.assertIn("溪谷餐廳", names)
        self.assertIn("森林民宿", names)
        self.assertEqual(len([stop for stop in result if "中午" in stop["time"]]), 2)
        self.assertEqual(len([stop for stop in result if "晚上" in stop["time"]]), 1)
        self.assertEqual(len([stop for stop in result if "夜間" in stop["time"]]), 1)

    def test_unknown_meal_and_lodging_names_become_safe_arrangements(self):
        stops = [
            {"kind": "other", "name": "AI 猜的午餐店", "time": "第1天中午", "note": ""},
            {"kind": "other", "name": "AI 猜的晚餐店", "time": "第1天晚上", "note": ""},
            {"kind": "other", "name": "AI 猜的民宿", "time": "第1天夜間", "note": ""},
        ]

        result = _normalize_unknown_arrangements(stops, {"merchants.json": []})

        self.assertEqual(
            [stop["name"] for stop in result],
            ["午餐安排", "晚餐安排", "住宿安排"],
        )

    def test_unknown_meal_and_lodging_use_real_context_candidates(self):
        context = {
            "merchants.json": [
                {"name": "山景餐廳", "category": "餐廳"},
                {"name": "溪谷餐廳", "category": "餐廳"},
                {"name": "森林民宿", "category": "民宿"},
            ]
        }
        stops = [
            {"kind": "other", "name": "AI 猜的午餐店", "time": "第1天中午", "note": ""},
            {"kind": "other", "name": "AI 猜的民宿", "time": "第1天晚上", "note": ""},
            {"kind": "other", "name": "AI 猜的晚餐店", "time": "第1天晚上", "note": ""},
        ]

        result = _normalize_unknown_arrangements(stops, context)

        self.assertEqual(
            [stop["name"] for stop in result],
            ["山景餐廳", "森林民宿", "溪谷餐廳"],
        )
        self.assertEqual(result[1]["time"], "第1天夜間")

    def test_unknown_other_attraction_is_not_silently_allowed(self):
        stops = [
            {"kind": "other", "name": "不存在的景點", "time": "第1天上午", "note": ""},
        ]

        result = _normalize_unknown_arrangements(stops, {"merchants.json": []})

        self.assertEqual(result[0]["name"], "不存在的景點")

    def test_day_trip_does_not_force_lodging(self):
        stops = [{"kind": "attraction", "id": "1", "time": "上午", "note": ""}]
        self.assertEqual(_ensure_overnight_basics(stops, "安排一日遊", {}), stops)

    def test_saved_plan_traffic_uses_all_stops_and_history_departure(self):
        stops = [
            {"name": "角板山公園"},
            {"name": "泰雅小棧特色料理"},
            {"name": "小烏來天空步道"},
        ]
        history = [{"role": "user", "parts": [{"text": "我從桃園火車站出發，搭公車"}]}]

        answer = _plan_traffic_reply(stops, "按照我的行程告訴我怎麼搭", history)

        self.assertIn("桃園火車站", answer)
        self.assertIn("角板山公園", answer)
        self.assertIn("泰雅小棧特色料理", answer)
        self.assertIn("小烏來天空步道", answer)
        self.assertIn("travelmode=transit", answer)
        self.assertNotIn("請補充出發地和目的地", answer)
        first_url = next(line for line in answer.splitlines() if line.startswith("https://www.google.com/maps/dir/"))
        query = parse_qs(urlparse(first_url).query)
        self.assertEqual(query["origin"], ["桃園火車站"])
        self.assertEqual(query["destination"], ["桃園市復興區角板山公園"])

    def test_saved_plan_traffic_does_not_require_departure(self):
        stops = [{"name": "角板山公園"}, {"name": "小烏來天空步道"}]
        answer = _plan_traffic_reply(stops, "照行程告訴我怎麼搭")
        self.assertIn("先列出行程各站之間", answer)
        self.assertIn("角板山公園 → 小烏來天空步道", answer)
        self.assertNotIn("請補充", answer)

    def test_saved_plan_traffic_routes_before_ai_provider(self):
        core._sessions["trip"] = (
            time.monotonic(),
            [{"role": "user", "parts": [{"text": "從桃園火車站出發，搭公車"}]}],
        )
        core._plans["trip"] = [
            {"name": "角板山公園"},
            {"name": "小烏來天空步道"},
        ]

        with patch("modules.ai_service.groq_reply.enabled", return_value=True), patch(
            "modules.ai_service.openai_reply.create_text_response"
        ) as provider:
            answer = get_groq_reply("按照目前行程告訴我怎麼搭", session_id="trip")

        self.assertIn("桃園火車站", answer)
        self.assertIn("角板山公園 → 小烏來天空步道", answer)
        provider.assert_not_called()

    def test_multiday_small_context_keeps_food_and_lodging(self):
        context = {
            "attractions": {"items": [{"id": "1", "name": "景點"}]},
            "merchants.json": (
                [{"name": f"民宿{i}", "category": "民宿"} for i in range(6)]
                + [{"name": f"餐廳{i}", "category": "餐廳"} for i in range(6)]
            ),
            "current_plan": [],
        }

        result = small_context(context, "安排兩天一夜行程")
        categories = {item["category"] for item in result["merchants.json"]}

        self.assertEqual(categories, {"餐廳", "民宿"})


if __name__ == "__main__":
    unittest.main()
