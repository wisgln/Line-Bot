import unittest
import json
from unittest.mock import patch
from modules.ai_service.traffic_cards import get_traffic_card
from modules.ai_service.info_cards import get_info_card


class TrafficCardsTests(unittest.TestCase):
    def rendered(self, query):
        return json.dumps(json.loads(get_traffic_card(query).to_json()), ensure_ascii=False)

    def test_bus_destination(self):
        result = self.rendered("從桃園火車站到小烏來怎麼搭車？")
        self.assertIn("502", result)
        self.assertIn("假日", result)
        self.assertNotIn("5090", result)

    def test_mountain_asks_destination(self):
        result = self.rendered("拉拉山怎麼搭車")
        self.assertIn("上巴陵", result)
        self.assertIn("交通字卡:lalashan:bus", result)
        self.assertNotIn("502", result)

    def test_forest_connection_warning(self):
        result = self.rendered("拉拉山森林遊樂區公車")
        self.assertIn("林班口", result)
        self.assertIn("並非直達", result)

    def test_driving_uri(self):
        result = self.rendered("交通字卡:lalashan:car")
        self.assertIn("travelmode=driving", result)
        self.assertNotIn("502", result)

    def test_road(self):
        self.assertIn("168.thb.gov.tw", self.rendered("小烏來封路嗎"))

    def test_unknown_and_multiple(self):
        self.assertIsNone(get_traffic_card("台北怎麼去"))
        for query in ("交通", "角板山到小烏來怎麼搭車"):
            self.assertIn("想去哪裡", self.rendered(query))

    def test_other_queries(self):
        for query in ("小烏來", "餐廳", "拉拉山有什麼特色", "安排角板山一日遊，開車"):
            self.assertIsNone(get_traffic_card(query))

    def test_bad_command(self):
        self.assertEqual(get_traffic_card("交通字卡:hack:bus").type, "text")

    def test_all_buttons(self):
        for destination in ("jiaobanshan", "xiaowulai", "lalashan", "baling"):
            for mode in ("choose", "bus", "car", "road", "detail"):
                self.assertEqual(get_traffic_card(f"交通字卡:{destination}:{mode}").type, "flex")

    def test_info_routing(self):
        self.assertEqual(get_info_card("交通字卡:xiaowulai:bus").type, "flex")

    def test_data_unavailable(self):
        with patch("modules.ai_service.traffic_cards.load_traffic", side_effect=ValueError):
            self.assertIn("官方查詢", self.rendered("小烏來公車"))


if __name__ == "__main__":
    unittest.main()
