import unittest

from modules.ai_service.compact_context import (
    compact_context,
    json_text,
    MAX_CONTEXT_CHARS,
)


class CompactContextTests(unittest.TestCase):
    def data(self):
        return {
            "attractions": {
                "status": "available",
                "items": [
                    {
                        "id": number,
                        "name": f"測試景點{number}",
                        "category": "自然",
                        "address": "桃園市復興區",
                        "description": "景點介紹" * 300,
                        "latitude": 24.8,
                        "longitude": 121.3,
                        "image_url": "https://example.com/image.jpg",
                        "maps_url": "https://example.com/map",
                        "phone": "000",
                    }
                    for number in range(1, 33)
                ],
            },
            "merchants.json": [
                {
                    "id": f"m{number}",
                    "name": f"測試商家{number}",
                    "category": "餐廳" if number <= 20 else "民宿",
                    "description": "店家介紹" * 200,
                    "price_items": [
                        {"name": "套餐", "price": 500, "unit": "套"},
                        {"name": "單點", "price": 100, "unit": "份"},
                    ],
                    "source_checked_on": "2026-10-01",
                }
                for number in range(1, 41)
            ],
            "faq.json": [{"question": "怎麼用", "answer": "使用說明"}],
            "local_products.json": [
                {"name": "水蜜桃", "description": "農產介紹"}
            ],
            "events": {"status": "reference_only", "items": []},
            "current_plan": [],
        }

    def test_budget_and_no_unrelated_sections(self):
        result = compact_context(self.data(), "幫我排一日遊")

        self.assertLessEqual(len(json_text(result)), MAX_CONTEXT_CHARS)
        self.assertLessEqual(len(result["attractions"]["items"]), 8)
        self.assertNotIn("faq.json", result)
        self.assertNotIn("local_products.json", result)
        self.assertTrue(
            all(item["category"] == "餐廳"
                for item in result["merchants.json"])
        )

    def test_pinned_itinerary_is_preserved(self):
        raw = self.data()
        raw["current_plan"] = [{
            "kind": "attraction",
            "id": "32",
            "name": "測試景點32",
            "time": "上午",
            "note": "原行程",
        }]

        result = compact_context(raw, "第二站換掉")
        ids = {str(item["id"]) for item in result["attractions"]["items"]}

        self.assertIn("32", ids)
        self.assertEqual(result["current_plan"], raw["current_plan"])

    def test_explicit_attraction_survives_selection(self):
        result = compact_context(self.data(), "介紹測試景點32")
        ids = {str(item["id"]) for item in result["attractions"]["items"]}
        self.assertIn("32", ids)

    def test_large_fields_removed_and_links_on_request(self):
        raw = self.data()
        normal = compact_context(raw, "介紹測試景點32")
        item = next(
            item for item in normal["attractions"]["items"]
            if item["id"] == 32
        )

        for key in ("latitude", "longitude", "image_url", "maps_url", "phone"):
            self.assertNotIn(key, item)

        linked = compact_context(raw, "測試景點32的地圖")
        item = next(
            item for item in linked["attractions"]["items"]
            if item["id"] == 32
        )
        self.assertEqual(item["maps_url"], "https://example.com/map")

    def test_prices_keep_units_and_date(self):
        result = compact_context(self.data(), "推薦餐廳")
        item = result["merchants.json"][0]

        self.assertEqual(item["price_items"][0]["unit"], "套")
        self.assertEqual(item["price_items"][1]["unit"], "份")
        self.assertEqual(item["source_checked_on"], "2026-10-01")
        self.assertNotIn("price_range", item)

    def test_related_product_is_included(self):
        result = compact_context(self.data(), "水蜜桃是什麼農特產")
        self.assertIn("local_products.json", result)
        self.assertEqual(result["attractions"]["items"], [])


if __name__ == "__main__":
    unittest.main()