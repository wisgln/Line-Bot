import json
import unittest
from unittest.mock import MagicMock, patch

from modules.ai_service.openai_reply import get_openai_reply
from modules.ai_service import get_reply
from modules.ai_service.ai_service import FALLBACK


class OpenAITests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict('os.environ', {
            'OPENAI_ENABLED': 'true', 'OPENAI_API_KEY': 'test-key',
            'OPENAI_MODEL': 'gpt-4.1-mini',
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_disabled_and_missing_key(self):
        for values in ({'OPENAI_ENABLED': 'false'}, {'OPENAI_API_KEY': ''}):
            with self.subTest(values=values), patch.dict('os.environ', values), patch('modules.ai_service.openai_reply.urlopen') as call:
                self.assertIsNone(get_openai_reply('旅遊建議'))
                call.assert_not_called()

    def test_request_and_response(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': '你想安排幾天呢？'}]}],
        }).encode()
        with patch('modules.ai_service.openai_reply.build_context', return_value={'public': 'data'}), patch('modules.ai_service.openai_reply.urlopen', return_value=response) as call:
            self.assertIn('你想安排幾天呢', get_openai_reply('幫我規劃旅行'))
            request = call.call_args.args[0]
            payload = json.loads(request.data)
            self.assertFalse(payload['store'])
            self.assertEqual(payload['model'], 'gpt-4.1-mini')
            self.assertEqual(json.loads(payload['input'])['question'], '幫我規劃旅行')
            self.assertNotIn('test-key', payload['input'])
            self.assertEqual(call.call_args.kwargs['timeout'], 15)

    def test_network_failure(self):
        with patch('modules.ai_service.openai_reply.build_context', return_value={}), patch('modules.ai_service.openai_reply.urlopen', side_effect=TimeoutError):
            self.assertIsNone(get_openai_reply('旅遊建議'))

    def test_incomplete_response(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"status":"incomplete","output":[]}'
        with patch('modules.ai_service.openai_reply.build_context', return_value={}), patch('modules.ai_service.openai_reply.urlopen', return_value=response):
            self.assertIsNone(get_openai_reply('旅遊建議'))

    def test_unknown_routes_to_ai_and_falls_back(self):
        with patch('modules.ai_service.gemini_reply.get_gemini_reply', return_value='AI answer') as call:
            self.assertEqual(get_reply('幫我整理旅行準備清單'), 'AI answer')
            call.assert_called_once()
        with patch('modules.ai_service.gemini_reply.get_gemini_reply', return_value=None):
            self.assertEqual(get_reply('幫我整理旅行準備清單'), FALLBACK)

    def test_known_query_bypasses_ai(self):
        with patch('modules.ai_service.openai_reply.get_openai_reply') as call:
            get_reply('需要下載App嗎')
            get_reply('推薦餐廳')
            call.assert_not_called()

    def test_context_failure_no_request(self):
        with patch('modules.ai_service.openai_reply.build_context', side_effect=ValueError), patch('modules.ai_service.openai_reply.urlopen') as call:
            self.assertIsNone(get_openai_reply('旅遊建議'))
            call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
