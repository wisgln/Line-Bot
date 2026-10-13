
# 泰雅文化 Quiz 題庫
QUIZ_QUESTIONS = [
    {
        "id": "quiz001",
        "question": "桃園市復興區是哪一個原住民族的重要聚居地？",
        "options": {
            "A": "阿美族",
            "B": "泰雅族",
            "C": "排灣族",
            "D": "布農族"
        },
        "answer": "B",
        "explanation": "桃園市復興區是泰雅族的重要聚居地之一，具有豐富的泰雅文化與部落歷史。"
    }
]


def get_quiz_question(quiz_id):
    """依照題目 ID 取得 Quiz。"""

    for quiz in QUIZ_QUESTIONS:
        if quiz["id"] == quiz_id:
            return quiz

    return None


def check_quiz_answer(quiz_id, user_answer):
    """判斷使用者答案是否正確。"""

    quiz = get_quiz_question(quiz_id)

    if quiz is None:
        return {
            "correct": False,
            "message": "找不到這道題目"
        }

    user_answer = user_answer.strip().upper()

    if user_answer not in quiz["options"]:
        return {
            "correct": False,
            "message": "請選擇 A、B、C 或 D"
        }

    is_correct = user_answer == quiz["answer"]

    return {
        "correct": is_correct,
        "message": "答對了！" if is_correct else "答錯了！",
        "correct_answer": quiz["answer"],
        "explanation": quiz["explanation"]
    }

def create_quiz_flex(quiz_id):
    """建立 LINE Quiz 選擇題 Flex Message。"""

    quiz = get_quiz_question(quiz_id)

    if quiz is None:
        return None

    buttons = []

    for option, answer_text in quiz["options"].items():
        buttons.append({
            "type": "button",
            "style": "secondary",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": f"{option}. {answer_text}",
                "data": f"culture_quiz:{quiz_id}:{option}",
                "displayText": f"我選擇 {option}. {answer_text}"
            }
        })

    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "泰雅文化知識挑戰",
                    "weight": "bold",
                    "size": "xl",
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": quiz["question"],
                    "size": "md",
                    "wrap": True
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": buttons
        }
    }
