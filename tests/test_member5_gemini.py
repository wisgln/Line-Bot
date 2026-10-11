import json
import io
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from modules.ai_service import get_reply
from modules.ai_service import gemini_reply as g


class GeminiTests(unittest.TestCase):
    def test_gemini3_parameters(self):
        with patch.dict('os.environ', {'GEMINI_MODEL': 'gemini-3.8-flash'}), patch.object(g, 'build_context', return_value={}), patch.object(g, 'urlopen', return_value=self.response()) as call:
            g.get_gemini_reply('規劃旅行')
            request = call.call_args.args[0]
            self.assertIn('gemini-3.8-flash:generateContent', request.full_url)
            self.assertEqual(json.loads(request.data)['generationConfig']['thinkingConfig'], {'thinkingLevel': 'low'})

    def test_safe_diagnostics(self):
        for code, reason, expected in ((400, 'API_KEY_INVALID', 'API_KEY_INVALID'), (403, 'SERVICE_DISABLED', 'SERVICE_DISABLED'), (404, '', 'HTTP 404'), (403, '', 'HTTP 403'), (401, '', 'HTTP 401'), (400, '', 'HTTP 400')):
            body = json.dumps({'error': {'message': 'secret-key', 'details': [{'reason': reason}]}}).encode()
            reply = g.configuration_error(HTTPError('url', code, '', {}, io.BytesIO(body)))
            self.assertIn(expected, reply)
            self.assertNotIn('secret-key', reply)

    def setUp(self):
        g._sessions.clear()
        env = patch.dict('os.environ', {'GEMINI_ENABLED': 'true', 'GEMINI_API_KEY': 'fake', 'GEMINI_MODEL': 'gemini-2.5-flash'}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(g._sessions.clear)

    def response(self, text='請問從哪裡出發？'):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}]}).encode()
        return response

    def test_history_isolation_and_reset(self):
        with patch.object(g, 'build_context', return_value={}), patch.object(g, 'urlopen', return_value=self.response()) as call:
            get_reply('有老人小孩，排一日行程推薦餐廳住宿', session_id='A')
            get_reply('我們開車，不想走很多路', session_id='A')
            body = json.loads(call.call_args.args[0].data)
            self.assertEqual(len(body['contents']), 3)
            self.assertIn('老人小孩', body['contents'][0]['parts'][0]['text'])
            get_reply('規劃旅遊', session_id='B')
            self.assertEqual(len(json.loads(call.call_args.args[0].data)['contents']), 1)
            get_reply('清除對話', session_id='A')
            self.assertFalse(g.has_session('A'))
            self.assertTrue(g.has_session('B'))

    def test_emergency_overrides_active_ai(self):
        g._sessions['A'] = (g.time.monotonic(), [])
        with patch.object(g, 'urlopen') as call:
            self.assertIn('119', get_reply('有人受傷需要救護車', session_id='A'))
            call.assert_not_called()

    def test_quota_does_not_save_or_retry(self):
        with patch.object(g, 'build_context', return_value={}), patch.object(g, 'urlopen', side_effect=HTTPError('url', 429, '', {}, None)) as call:
            self.assertIn('使用限制', g.get_gemini_reply('規劃旅行', session_id='A'))
            call.assert_called_once()
            self.assertFalse(g.has_session('A'))

    def test_disabled(self):
        with patch.dict('os.environ', {'GEMINI_ENABLED': 'false'}), patch.object(g, 'urlopen') as call:
            self.assertIsNone(g.get_gemini_reply('規劃旅行'))
            call.assert_not_called()

    def test_expiry(self):
        g._sessions['A'] = (0, [])
        with patch.object(g.time, 'monotonic', return_value=g.TTL + 1):
            self.assertFalse(g.has_session('A'))

    def test_history_bounded(self):
        with patch.object(g, 'build_context', return_value={}), patch.object(g, 'urlopen', return_value=self.response()):
            for i in range(12):
                g.get_gemini_reply(str(i), session_id='A')
            self.assertEqual(len(g._sessions['A'][1]), g.MAX_MESSAGES)

    def test_no_session_no_shared_history(self):
        with patch.object(g, 'build_context', return_value={}), patch.object(g, 'urlopen', return_value=self.response()):
            g.get_gemini_reply('規劃旅行')
            self.assertFalse(g._sessions)

    def test_empty_candidates(self):
        response = self.response()
        response.__enter__.return_value.read.return_value = b'{"candidates":[]}'
        with patch.object(g, 'build_context', return_value={}), patch.object(g, 'urlopen', return_value=response):
            self.assertIn('NO_CANDIDATES', g.get_gemini_reply('規劃旅行'))

    def test_timeout_distinct_from_network(self):
        from urllib.error import URLError
        for error, code in ((TimeoutError(), 'TIMEOUT'), (URLError(TimeoutError()), 'TIMEOUT'), (URLError('private diagnostic'), 'NETWORK')):
            with patch.object(g, 'build_context', return_value={}), patch.object(g, 'urlopen', side_effect=error):
                reply = g.get_gemini_reply('規劃旅行')
                self.assertIn(code, reply)
                self.assertNotIn('private diagnostic', reply)

    def test_truncated_response(self):
        response = self.response()
        response.__enter__.return_value.read.return_value = b'{"candidates":[{"finishReason":"MAX_TOKENS"}]}'
        with patch.object(g, 'build_context', return_value={}), patch.object(g, 'urlopen', return_value=response):
            self.assertIn('MAX_TOKENS', g.get_gemini_reply('規劃旅行', session_id='A'))
            self.assertFalse(g.has_session('A'))
