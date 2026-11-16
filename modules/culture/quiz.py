
# 泰雅文化 Quiz 題庫：共 10 題

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
    },
    {
        "id": "quiz006",
        "question": "泰雅族部分傳統織布上的菱形紋，常被詮釋為什麼？",
        "options": {
            "A": "交通標誌",
            "B": "祖靈之眼",
            "C": "現代建築",
            "D": "海洋波浪"
        },
        "answer": "B",
        "explanation": "在部分泰雅族文化詮釋中，織布上的菱形紋象徵祖靈之眼，與祖靈的守護及提醒有關。"
    },
    {
        "id": "quiz007",
        "question": "在泰雅族部分傳統傳說中，彩虹橋象徵什麼？",
        "options": {
            "A": "現代公路",
            "B": "城市入口",
            "C": "通往祖靈世界的道路",
            "D": "商店街"
        },
        "answer": "C",
        "explanation": "在部分泰雅族傳統敘事中，彩虹橋象徵通往祖靈世界的道路。不同部落的故事版本可能有所差異。"
    },
    {
        "id": "quiz008",
        "question": "小烏來風景特定區以哪一項景觀聞名？",
        "options": {
            "A": "瀑布與天空步道",
            "B": "沙漠與沙丘",
            "C": "珊瑚礁",
            "D": "都市摩天大樓"
        },
        "answer": "A",
        "explanation": "小烏來位於桃園市復興區，以小烏來瀑布、天空步道及溪谷自然景觀聞名。"
    },
    {
        "id": "quiz009",
        "question": "下列哪一組是桃園市復興區的部落或地區名稱？",
        "options": {
            "A": "西門町與信義商圈",
            "B": "羅浮與溪口",
            "C": "墾丁與恆春",
            "D": "淡水與八里"
        },
        "answer": "B",
        "explanation": "羅浮與溪口是桃園市復興區的地區及部落名稱，當地具有泰雅族文化特色。"
    },
    {
        "id": "quiz010",
        "question": "泰雅族 Gaya 所重視的觀念，與下列哪一項最接近？",
        "options": {
            "A": "只追求個人利益",
            "B": "不需要遵守任何規範",
            "C": "忽視祖先與文化傳承",
            "D": "尊重自然與群體規範"
        },
        "answer": "D",
        "explanation": "Gaya 涉及人與人、人與自然及祖先之間的關係，重視責任、尊重、合作與群體規範。"
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


def create_back_to_culture_button():
    """建立返回泰雅文化選單按鈕。"""
    return {
        "type": "button",
        "style": "secondary",
        "height": "sm",
        "action": {
            "type": "postback",
            "label": "返回泰雅文化選單",
            "data": "menu_culture",
            "displayText": "返回泰雅文化選單"
        }
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

    # 使用者不必答完所有題目才能離開
    buttons.append(create_back_to_culture_button())

    quiz_ids = [item["id"] for item in QUIZ_QUESTIONS]
    question_number = quiz_ids.index(quiz_id) + 1

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
                    "text": f"第 {question_number} / {len(QUIZ_QUESTIONS)} 題",
                    "size": "sm",
                    "color": "#777777"
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


def get_next_quiz_id(current_quiz_id):
    """取得下一題 ID；最後一題回傳 None。"""

    quiz_ids = [quiz["id"] for quiz in QUIZ_QUESTIONS]

    if current_quiz_id not in quiz_ids:
        return None

    current_index = quiz_ids.index(current_quiz_id)
    next_index = current_index + 1

    if next_index >= len(quiz_ids):
        return None

    return quiz_ids[next_index]


def create_next_quiz_button(current_quiz_id):
    """建立下一題或挑戰完成的 LINE 按鈕。"""

    next_id = get_next_quiz_id(current_quiz_id)

    if next_id is None:
        return {
            "type": "button",
            "style": "primary",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": "挑戰完成",
                "data": "menu_culture",
                "displayText": "返回泰雅文化探索"
            }
        }

    return {
        "type": "button",
        "style": "primary",
        "height": "sm",
        "action": {
            "type": "postback",
            "label": "下一題",
            "data": f"culture_quiz_next:{next_id}",
            "displayText": "繼續挑戰下一題"
        }
    }


def create_quiz_result_flex(quiz_id, user_answer):
    """建立 Quiz 答題結果與下一題按鈕。"""

    quiz = get_quiz_question(quiz_id)

    if quiz is None:
        return None

    result = check_quiz_answer(quiz_id, user_answer)

    if "correct_answer" not in result:
        return None

    is_correct = result["correct"]
    title = "🎉 答對了！" if is_correct else "💡 答錯了！"

    correct_answer = result["correct_answer"]
    answer_text = quiz["options"][correct_answer]

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
                    "text": title,
                    "weight": "bold",
                    "size": "xl",
                    "color": "#256D5B"
                },
                {
                    "type": "text",
                    "text": quiz["question"],
                    "wrap": True,
                    "size": "md"
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"正確答案：{correct_answer}. {answer_text}",
                    "weight": "bold",
                    "wrap": True,
                    "size": "md"
                },
                {
                    "type": "text",
                    "text": result["explanation"],
                    "wrap": True,
                    "size": "sm",
                    "color": "#666666"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                create_next_quiz_button(quiz_id),
                create_back_to_culture_button()
            ]
        }
    }
