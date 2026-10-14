
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
    },
    {
        "id": "quiz002",
        "question": "泰雅族傳統織布常使用哪一種材料？",
        "options": {
            "A": "苧麻",
            "B": "塑膠",
            "C": "玻璃",
            "D": "金屬"
        },
        "answer": "A",
        "explanation": "泰雅族傳統織布常使用苧麻纖維，透過紡線、染色與織造製作織品。"
    },
    {
        "id": "quiz003",
        "question": "泰雅族文化中的 Gaya 主要代表什麼？",
        "options": {
            "A": "現代交通工具",
            "B": "傳統規範與倫理觀念",
            "C": "外國語言",
            "D": "商業品牌"
        },
        "answer": "B",
        "explanation": "Gaya 是泰雅族重要的傳統規範與倫理觀念，涉及責任、尊重、合作及群體秩序。"
    },
    {
        "id": "quiz004",
        "question": "泰雅族不同部落的歷史故事通常與哪一項有關？",
        "options": {
            "A": "祖源與遷徙歷程",
            "B": "太空旅行",
            "C": "現代電腦製造",
            "D": "國際股票市場"
        },
        "answer": "A",
        "explanation": "泰雅族不同部落有各自的祖源與遷徙故事，反映族群歷史以及與土地的連結。"
    },
    {
        "id": "quiz005",
        "question": "認識角板山及復興區泰雅文化時，應該重視什麼？",
        "options": {
            "A": "只注意拍照打卡",
            "B": "忽略部落生活規範",
            "C": "尊重在地文化與部落生活",
            "D": "任意進入私人場所"
        },
        "answer": "C",
        "explanation": "參訪角板山與復興區時，應尊重在地文化、部落生活空間及文化規範。"
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
