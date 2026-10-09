import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import requests

from modules.weather import weather_service as weather


def make_period(start, end, description="多雲，降雨機率 20%。"):
    return {
        "StartTime": start,
        "EndTime": end,
        "ElementValue": [{"WeatherDescription": description}],
    }


def make_data(periods, city="桃園市", district="復興區"):
    return {
        "success": "true",
        "records": {
            "Locations": [
                {
                    "LocationsName": city,
                    "Location": [
                        {
                            "LocationName": district,
                            "WeatherElement": [{"Time": periods}],
                        }
                    ],
                }
            ]
        },
    }


class WeatherParsingTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(
            2026, 10, 8, 12, 0,
            tzinfo=weather.TAIWAN_TIME,
        )

    def test_time_without_timezone(self):
        result = weather.parse_time("2026-10-08T12:00:00")
        self.assertEqual(result, self.now)
        self.assertEqual(result.utcoffset(), self.now.utcoffset())

    def test_utc_time_converted_to_taiwan(self):
        result = weather.parse_time("2026-10-08T04:00:00+00:00")
        self.assertEqual(result, self.now)
        self.assertEqual(result.hour, 12)
        self.assertEqual(result.utcoffset(), self.now.utcoffset())

    def test_invalid_time(self):
        with self.assertRaises(ValueError):
            weather.parse_time("not-a-time")

    def test_only_fuxing_in_taoyuan(self):
        period = make_period(
            "2026-10-08T12:00:00",
            "2026-10-08T15:00:00",
        )
        data = make_data([period])

        other_city = make_data(
            [period], city="其他縣市"
        )["records"]["Locations"][0]
        data["records"]["Locations"].append(other_city)

        other_district = make_data(
            [period], district="桃園區"
        )["records"]["Locations"][0]["Location"][0]
        data["records"]["Locations"][0]["Location"].append(
            other_district
        )

        result = weather.extract_forecasts(data, self.now)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][2], "多雲，降雨機率 20%。")

    def test_expired_and_invalid_periods_are_excluded(self):
        data = make_data([
            make_period(
                "2026-10-08T09:00:00",
                "2026-10-08T12:00:00",
                "已結束",
            ),
            make_period(
                "2026-10-08T15:00:00",
                "2026-10-08T15:00:00",
                "零長度",
            ),
            make_period(
                "2026-10-08T18:00:00",
                "2026-10-08T15:00:00",
                "時間顛倒",
            ),
            make_period(
                "2026-10-08T11:00:00",
                "2026-10-08T14:00:00",
                "進行中",
            ),
        ])

        result = weather.extract_forecasts(data, self.now)
        self.assertEqual(
            [item[2] for item in result],
            ["進行中"],
        )

    def test_sorted_and_limited_to_three(self):
        periods = [
            make_period(
                f"2026-10-08T{hour:02d}:00:00",
                f"2026-10-08T{hour + 1:02d}:00:00",
                f"時段{hour}",
            )
            for hour in (18, 12, 21, 15)
        ]

        result = weather.extract_forecasts(
            make_data(periods), self.now
        )
        self.assertEqual(
            [item[0].hour for item in result],
            [12, 15, 18],
        )

    def test_missing_description_is_skipped(self):
        period = make_period(
            "2026-10-08T12:00:00",
            "2026-10-08T15:00:00",
        )
        period["ElementValue"] = [{"Temperature": "20"}]

        result = weather.extract_forecasts(
            make_data([period]), self.now
        )
        self.assertEqual(result, [])


class WeatherReplyTests(unittest.TestCase):
    def setUp(self):
        # 阻止讀取本機 .env，並使用假的授權碼。
        dotenv_patch = patch.object(weather, "load_dotenv")
        dotenv_patch.start()
        self.addCleanup(dotenv_patch.stop)

        env_patch = patch.dict(
            weather.os.environ,
            {"WEATHER_API_KEY": "test-key-only"},
        )
        env_patch.start()
        self.addCleanup(env_patch.stop)

        # 攔截 Session，所有請求都使用模擬回應。
        session_patch = patch.object(weather.requests, "Session")
        self.session_class = session_patch.start()
        self.addCleanup(session_patch.stop)
        self.session = (
            self.session_class.return_value
            .__enter__.return_value
        )

        self.response = Mock()
        self.response.status_code = 200
        self.response.raise_for_status.return_value = None
        self.response.json.return_value = make_data([
            make_period(
                "2026-10-08T12:00:00",
                "2026-10-08T15:00:00",
            )
        ])
        self.session.get.return_value = self.response

        # 固定現在時間，避免測試隨日期改變而失敗。
        clock_patch = patch.object(weather, "datetime")
        self.clock = clock_patch.start()
        self.addCleanup(clock_patch.stop)
        self.clock.now.return_value = datetime(
            2026, 10, 8, 12, 0,
            tzinfo=weather.TAIWAN_TIME,
        )
        self.clock.fromisoformat.side_effect = (
            datetime.fromisoformat
        )

    def test_successful_reply(self):
        reply = weather.get_weather_reply()

        self.assertIn("桃園市復興區", reply)
        self.assertIn("10/08 12:00～10/08 15:00", reply)
        self.assertIn("多雲，降雨機率 20%。", reply)
        self.assertIn("查詢時間：10/08 12:00", reply)
        self.assertIn("非即時觀測", reply)
        self.assertNotIn("test-key-only", reply)

    def test_missing_key_does_not_connect(self):
        with patch.dict(
            weather.os.environ,
            {"WEATHER_API_KEY": "   "},
        ):
            reply = weather.get_weather_reply()

        self.assertIn("尚未設定 WEATHER_API_KEY", reply)
        self.session_class.assert_not_called()

    def test_authorization_failure(self):
        for status in (401, 403):
            with self.subTest(status=status):
                self.response.status_code = status
                self.assertIn(
                    "授權未通過",
                    weather.get_weather_reply(),
                )

    def test_rate_limit(self):
        self.response.status_code = 429
        self.assertIn(
            "次數暫時達到限制",
            weather.get_weather_reply(),
        )

    def test_timeout(self):
        self.session.get.side_effect = requests.Timeout()
        self.assertIn("逾時", weather.get_weather_reply())

    def test_connection_error_hides_sensitive_details(self):
        self.session.get.side_effect = requests.ConnectionError(
            "https://example.invalid/?Authorization=test-key-only"
        )

        reply = weather.get_weather_reply()

        self.assertIn("ConnectionError", reply)
        self.assertNotIn("test-key-only", reply)
        self.assertNotIn("https://", reply)

    def test_http_server_error(self):
        self.response.status_code = 500
        self.response.raise_for_status.side_effect = (
            requests.HTTPError(response=self.response)
        )

        reply = weather.get_weather_reply()

        self.assertIn("HTTPError", reply)
        self.assertIn("500", reply)

    def test_api_reports_failure(self):
        self.response.json.return_value = {"success": "false"}
        self.assertIn(
            "未成功回傳資料",
            weather.get_weather_reply(),
        )

    def test_unexpected_data_structure(self):
        self.response.json.return_value = {"success": "true"}
        self.assertIn(
            "資料格式與預期不符",
            weather.get_weather_reply(),
        )

    def test_no_valid_forecasts(self):
        self.response.json.return_value = make_data([])
        self.assertIn(
            "沒有取得復興區有效的預報時段",
            weather.get_weather_reply(),
        )


if __name__ == "__main__":
    unittest.main()