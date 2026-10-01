from .ai_service import get_reply

print("FAQ 測試模式（輸入 exit 離開）")
while True:
    try:
        question = input("你：")
    except (EOFError, KeyboardInterrupt):
        break
    if question.strip().casefold() == "exit":
        break
    print("Bot：" + get_reply(question))
