
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from handlers.postback_handler import handle_postback_event
from linebot.v3.messaging import TextMessage, FlexMessage


def test_postback(data, expected_type):
    event = SimpleNamespace(
        postback=SimpleNamespace(data=data),
        reply_token="test_token"
    )

    with patch("handlers.postback_handler.ApiClient"), \
         patch("handlers.postback_handler.MessagingApi") as mock_api:

        handle_postback_event(event, MagicMock())

        calls = mock_api.return_value.reply_message.call_args_list

        if len(calls) != 1:
            print(f"{data}：失敗，回覆次數 {len(calls)}")
            return False

        message = calls[0].args[0].messages[0]

        if isinstance(message, expected_type):
            print(f"{data}：成功")
            return True

        print(f"{data}：失敗，訊息類型 {type(message).__name__}")
        return False


if __name__ == "__main__":
    cases = [
        ("menu_culture", FlexMessage),
        ("culture_view:culture007", FlexMessage),
        ("culture_view:culture008", FlexMessage),
        ("culture_quiz:quiz001:B", FlexMessage),
        ("culture_quiz_next:quiz002", FlexMessage),
        ("menu_nearby", TextMessage),
        ("menu_attraction", TextMessage),
        ("menu_ai", TextMessage),
    ]

    results = [
        test_postback(data, expected_type)
        for data, expected_type in cases
    ]

    print(f"\n測試結果：{sum(results)}/{len(results)} 通過")
