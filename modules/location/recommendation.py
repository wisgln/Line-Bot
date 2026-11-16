from modules.location.opening_status import get_opening_status


def calculate_recommendation_score(attraction, preferred_category=None):
    """
    計算景點推薦分數。

    目前考量：
    1. 距離
    2. 是否營業
    3. 使用者偏好的景點分類

    分數越高，推薦順位越前面。
    """

    score = 100.0

    # 1. 距離
    # 每多 1 km 扣 2 分
    distance = attraction.get("distance")

    if distance is not None:
        try:
            score -= float(distance) * 2
        except (TypeError, ValueError):
            pass

    # 2. 營業狀態
    opening_hours = attraction.get("opening_hours", "")
    opening_status = get_opening_status(opening_hours)

    if opening_status.startswith("🟢"):
        score += 40

    elif opening_status.startswith("🟡"):
        # 部分開放（例如戶外開放、室內休館），仍可前往，視同營業中
        score += 40

    elif opening_status.startswith("⚪"):
        # 資料不確定，不直接判定不好
        score += 5

    elif opening_status.startswith("🔴"):
        score -= 40

    # 3. 使用者偏好分類
    if preferred_category:
        if attraction.get("category") == preferred_category:
            score += 20

    # 預留未來評分功能
    rating = attraction.get("rating")

    if isinstance(rating, (int, float)):
        score += rating * 5

    return round(score, 2)


def rank_attractions(attractions, preferred_category=None):
    """
    對景點進行智慧推薦排序。
    """

    ranked = []

    for attraction in attractions:
        item = attraction.copy()

        item["recommendation_score"] = calculate_recommendation_score(
            item,
            preferred_category=preferred_category
        )

        ranked.append(item)

    ranked.sort(
        key=lambda item: (
            item["recommendation_score"],
            -item.get("distance", 9999)
        ),
        reverse=True
    )

    return ranked