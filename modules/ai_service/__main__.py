from pathlib import Path
from uuid import uuid4

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

from .ai_service import get_reply

print("旅遊問答測試模式（輸入 exit 離開，也可按 Ctrl+C）")
session_id = 'cli:' + uuid4().hex
print("輸入「清除對話」重設行程；對話記憶保留最近 8 輪、閒置 30 分鐘。")
while True:
    try:
        question = input("你：")
    except (EOFError, KeyboardInterrupt):
        break
    if question.strip().casefold() == "exit":
        break
    print("Bot：" + get_reply(question, session_id=session_id))
