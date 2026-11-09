import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from modules.ai_service.openai_reply import get_openai_reply
from modules.ai_service.openai_reply import (
    ITINERARY_FORMAT,
    create_json_response,
    create_text_response,
)
from modules.ai_service import get_reply
from modules.ai_service.ai_service import FALLBACK
from modules.ai_service import gemini_reply as planning_core


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

    def test_openai_is_primary_planning_provider(self):
        with patch(
            'modules.ai_service.groq_reply.get_groq_reply',
            return_value='OpenAI itinerary',
        ) as call:
            self.assertTrue(planning_core.enabled())
            self.assertEqual(
                planning_core.get_gemini_reply('幫我排一日遊'),
                'OpenAI itinerary',
            )
            call.assert_called_once_with('幫我排一日遊', session_id=None)

    def test_structured_responses_request(self):
        response = SimpleNamespace(
            status='completed',
            output_text='{"action":"answer","message":"您好","stops":[]}',
        )
        client = MagicMock()
        client.__enter__.return_value.responses.create.return_value = response
        factory = MagicMock(return_value=client)
        module = SimpleNamespace(OpenAI=factory)
        messages = [
            {'role': 'system', 'content': '只輸出 JSON'},
            {'role': 'user', 'content': '安排一日遊'},
        ]

        with patch.dict(sys.modules, {'openai': module}):
            status, content = create_json_response(messages)

        self.assertEqual(status, 'completed')
        self.assertIn('"action":"answer"', content)
        request = client.__enter__.return_value.responses.create
        request.assert_called_once_with(
            model='gpt-4.1-mini',
            instructions='只輸出 JSON',
            input=messages[1:],
            text={'format': ITINERARY_FORMAT},
            max_output_tokens=2000,
            store=False,
        )
        factory.assert_called_once_with(
            api_key='test-key', timeout=30.0, max_retries=0
        )

    def test_text_responses_request_uses_small_output_budget(self):
        response = SimpleNamespace(
            status='completed',
            output_text='下雨可以優先安排室內文化景點。',
        )
        client = MagicMock()
        client.__enter__.return_value.responses.create.return_value = response
        factory = MagicMock(return_value=client)
        module = SimpleNamespace(OpenAI=factory)
        messages = [
            {'role': 'system', 'content': '精簡回答旅遊問題'},
            {'role': 'user', 'content': '下雨適合去哪裡？'},
        ]

        with patch.dict(sys.modules, {'openai': module}):
            status, content = create_text_response(messages)

        self.assertEqual(status, 'completed')
        self.assertIn('下雨', content)
        client.__enter__.return_value.responses.create.assert_called_once_with(
            model='gpt-4.1-mini',
            instructions='精簡回答旅遊問題',
            input=messages[1:],
            max_output_tokens=500,
            store=False,
        )


if __name__ == '__main__':
    unittest.main()
