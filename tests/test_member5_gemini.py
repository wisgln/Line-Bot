import io
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from modules.ai_service import get_reply
from modules.ai_service import gemini_reply as g


class GeminiTests(unittest.TestCase):
    def setUp(self):
        g._sessions.clear()
        g._plans.clear()

        self.addCleanup(g._sessions.clear)
        self.addCleanup(g._plans.clear)

        patches = [
            patch.dict(
                "os.environ",
                {
                    "GEMINI_ENABLED": "true",
                    "GEMINI_API_KEY": "offline-test-key",
                    "GEMINI_MODEL": "gemini-2.5-flash",
                },
                clear=True,
            ),
            patch.object(g, "build_context", return_value={}),
            patch.object(
                g,
                "load_attraction_context",
                return_value={"status": "available", "items": []},
            ),
            patch.object(
                g,
                "event_context",
                return_value={"status": "reference_only", "items": []},
            ),
            # 所有測試都封鎖真實連線。
            patch.object(g, "urlopen", return_value=self.response()),
        ]

        for patcher in patches:
            mocked = patcher.start()
            self.addCleanup(patcher.stop)

        self.api = mocked

    def response(self, text="請問從哪裡出發？"):
        """模擬 Gemini 外層回應，以及內層行程 JSON。"""
        answer = json.dumps(
            {"message": text, "stops": []},
            ensure_ascii=False,
        )

        payload = {
            "candidates": [
                {
                    "finishReason": "STOP",
                    "content": {
                        "parts": [{"text": answer}]
                    },
                }
            ]
        }

        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            json.dumps(payload, ensure_ascii=False).encode("utf-8")
        )
        return response

    def request_body(self):
        return json.loads(self.api.call_args.args[0].data)

    def test_gemini3_parameters(self):
        with patch.dict(
            "os.environ",
            {"GEMINI_MODEL": "gemini-3.8-flash"},
        ):
            reply = g.get_gemini_reply("規劃旅行")

        self.assertEqual(reply, "請問從哪裡出發？")
        request = self.api.call_args.args[0]

        self.assertIn(
            "gemini-3.8-flash:generateContent",
            request.full_url,
        )
        self.assertEqual(
            self.request_body()["generationConfig"]["thinkingConfig"],
            {"thinkingLevel": "low"},
        )

    def test_safe_diagnostics(self):
        cases = (
            (400, "API_KEY_INVALID", "API_KEY_INVALID"),
            (403, "SERVICE_DISABLED", "SERVICE_DISABLED"),
            (404, "", "HTTP 404"),
            (403, "", "HTTP 403"),
            (401, "", "HTTP 401"),
            (400, "", "HTTP 400"),
        )

        for code, reason, expected in cases:
            with self.subTest(code=code, reason=reason):
                body = json.dumps({
                    "error": {
                        "message": "secret-key",
                        "details": [{"reason": reason}],
                    }
                }).encode("utf-8")

                error = HTTPError(
                    "url", code, "", {}, io.BytesIO(body)
                )
                reply = g.configuration_error(error)

                self.assertIn(expected, reply)
                self.assertNotIn("secret-key", reply)

    def test_history_isolation_and_reset(self):
        first = get_reply(
            "有老人小孩，排一日行程推薦餐廳住宿",
            session_id="A",
        )
        self.assertEqual(first, "請問從哪裡出發？")
        self.assertTrue(g.has_session("A"))

        get_reply(
            "我們開車，不想走很多路",
            session_id="A",
        )

        body = self.request_body()
        self.assertEqual(len(body["contents"]), 3)
        self.assertEqual(
            [item["role"] for item in body["contents"]],
            ["user", "model", "user"],
        )
        self.assertIn(
            "老人小孩",
            body["contents"][0]["parts"][0]["text"],
        )
        self.assertIn(
            "我們開車",
            body["contents"][2]["parts"][0]["text"],
        )

        get_reply("規劃旅遊", session_id="B")
        self.assertEqual(
            len(self.request_body()["contents"]), 1
        )

        calls_before_reset = self.api.call_count
        get_reply("清除對話", session_id="A")

        self.assertEqual(self.api.call_count, calls_before_reset)
        self.assertFalse(g.has_session("A"))
        self.assertTrue(g.has_session("B"))
        self.assertNotIn("A", g._plans)

    def test_emergency_overrides_active_ai(self):
        g._sessions["A"] = (g.time.monotonic(), [])

        reply = get_reply(
            "有人受傷需要救護車",
            session_id="A",
        )

        self.assertIn("119", reply)
        self.api.assert_not_called()

    def test_quota_does_not_save_or_retry(self):
        self.api.side_effect = HTTPError(
            "url", 429, "", {}, None
        )

        reply = g.get_gemini_reply(
            "規劃旅行", session_id="A"
        )

        self.assertIn("使用限制", reply)
        self.api.assert_called_once()
        self.assertFalse(g.has_session("A"))
        self.assertEqual(g.get_saved_stops("A"), [])

    def test_disabled(self):
        with patch.dict(
            "os.environ",
            {"GEMINI_ENABLED": "false"},
        ):
            self.assertIsNone(g.get_gemini_reply("規劃旅行"))

        self.api.assert_not_called()

    def test_expiry(self):
        g._sessions["A"] = (0, [])
        g._plans["A"] = [{"kind": "other", "name": "休息"}]

        with patch.object(
            g.time,
            "monotonic",
            return_value=g.TTL + 1,
        ):
            self.assertFalse(g.has_session("A"))
            self.assertEqual(g.get_saved_stops("A"), [])

        self.assertNotIn("A", g._plans)

    def test_history_bounded(self):
        for number in range(12):
            reply = g.get_gemini_reply(
                str(number), session_id="A"
            )
            self.assertEqual(reply, "請問從哪裡出發？")

        history = g._sessions["A"][1]

        self.assertEqual(len(history), g.MAX_MESSAGES)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[-1]["role"], "model")
        self.assertEqual(
            history[-2]["parts"][0]["text"], "11"
        )

    def test_no_session_no_shared_history(self):
        for _ in range(2):
            reply = g.get_gemini_reply("規劃旅行")
            self.assertEqual(reply, "請問從哪裡出發？")
            self.assertEqual(
                len(self.request_body()["contents"]), 1
            )

        self.assertFalse(g._sessions)
        self.assertFalse(g._plans)

    def test_empty_candidates(self):
        self.api.return_value.__enter__.return_value.read.return_value = (
            b'{"candidates":[]}'
        )

        reply = g.get_gemini_reply(
            "規劃旅行", session_id="A"
        )

        self.assertIn("NO_CANDIDATES", reply)
        self.assertFalse(g.has_session("A"))

    def test_timeout_distinct_from_network(self):
        cases = (
            (TimeoutError(), "TIMEOUT"),
            (URLError(TimeoutError()), "TIMEOUT"),
            (URLError("private diagnostic"), "NETWORK"),
        )

        for error, code in cases:
            with self.subTest(code=code):
                self.api.side_effect = error

                reply = g.get_gemini_reply("規劃旅行")

                self.assertIn(code, reply)
                self.assertNotIn("private diagnostic", reply)

    def test_truncated_response(self):
        self.api.return_value.__enter__.return_value.read.return_value = (
            b'{"candidates":[{"finishReason":"MAX_TOKENS"}]}'
        )

        reply = g.get_gemini_reply(
            "規劃旅行", session_id="A"
        )

        self.assertIn("MAX_TOKENS", reply)
        self.assertFalse(g.has_session("A"))
        self.assertEqual(g.get_saved_stops("A"), [])

    def test_plain_text_is_not_saved_as_valid_plan(self):
        payload = {
            "candidates": [{
                "finishReason": "STOP",
                "content": {
                    "parts": [{"text": "不是JSON的舊格式回答"}]
                },
            }]
        }

        self.api.return_value.__enter__.return_value.read.return_value = (
            json.dumps(payload).encode("utf-8")
        )

        reply = g.get_gemini_reply(
            "規劃旅行", session_id="A"
        )

        self.assertEqual(reply, g.FORMAT_ERROR)
        self.assertFalse(g.has_session("A"))
        self.assertEqual(g.get_saved_stops("A"), [])


if __name__ == "__main__":
    unittest.main()