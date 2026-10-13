
from pathlib import Path
import json

# 專案根目錄
BASE_DIR = Path(__file__).resolve().parents[2]

# 泰雅文化資料檔案位置
CULTURE_DATA_PATH = BASE_DIR / "data" / "culture.json"


def load_culture_data():
    """讀取泰雅文化 JSON 資料。"""

    if not CULTURE_DATA_PATH.exists():
        return []

    with open(CULTURE_DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

def get_culture_by_id(culture_id):
    """根據文化 ID 查詢資料。"""

    cultures = load_culture_data()

    for culture in cultures:
        if culture.get("id") == culture_id:
            return culture

    return None
