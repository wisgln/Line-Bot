
import json
from pathlib import Path

# 取得專題根目錄
BASE_DIR = Path(__file__).resolve().parents[2]

# 景點資料檔案位置
DATA_PATH = BASE_DIR / "data" / "attractions.json"


# 功能一：讀取所有景點
def get_all_attractions():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        attractions = json.load(file)

    return attractions


# 功能二：取得所有景點分類
def get_categories():
    attractions = get_all_attractions()

    categories = []

    for attraction in attractions:
        category = attraction["category"]

        if category not in categories:
            categories.append(category)

    return categories


# 功能三：依照分類搜尋景點
def get_attractions_by_category(category):
    attractions = get_all_attractions()

    results = []

    for attraction in attractions:
        if attraction["category"] == category:
            results.append(attraction)

    return results


# 功能四：依照景點名稱搜尋
def search_attractions(keyword):
    attractions = get_all_attractions()

    results = []

    for attraction in attractions:
        if keyword.strip() in attraction["name"]:
            results.append(attraction)

    return results
