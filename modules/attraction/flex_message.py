
from urllib.parse import quote


# 建立單一景點的 Flex Message 卡片
def create_attraction_bubble(attraction):
    name = attraction.get("name", "未命名景點")
    category = attraction.get("category", "未分類")
    description = attraction.get("description", "暫無介紹")
    address = attraction.get("address", "暫無地址")
    phone = attraction.get("phone", "暫無電話")
    opening_hours = attraction.get("opening_hours", "暫無資訊")
    image_url = attraction.get("image_url", "")
    maps_url = attraction.get("maps_url", "")
    tags = attraction.get("tags", [])
    accessibility = attraction.get("accessibility", {})


    if not maps_url:
        maps_url = (
            "https://www.google.com/maps/search/?api=1&query="
            + quote(name)
        )

    contents = [
        {
            "type": "text",
            "text": name,
            "weight": "bold",
            "size": "xl",
            "wrap": True
        },
        {
            "type": "text",
            "text": category,
            "size": "sm",
            "color": "#888888"
        }
    ]

    # 顯示景點友善標籤
    if tags:
        contents.append({
            "type": "text",
            "text": "・".join(tags),
            "size": "sm",
            "color": "#168A60",
            "wrap": True,
            "margin": "md"
        })

    # 只有已查證的無障礙設施才顯示
    if isinstance(accessibility, dict):
        status = accessibility.get("status", "尚未查證")
        facilities = accessibility.get("facilities", [])

        if status == "已查證" and facilities:
            contents.append({
                "type": "text",
                "text": "♿ 無障礙設施：" + "、".join(facilities),
                "size": "sm",
                "color": "#3975B7",
                "wrap": True,
                "margin": "md"
            })

    # 景點基本資訊
    info = [
        ("景點介紹", description),
        ("地址", address),
        ("電話", phone),
        ("營業時間", opening_hours)
    ]

    for label, value in info:
        contents.append({
            "type": "text",
            "text": f"{label}：{value}",
            "size": "sm",
            "wrap": True,
            "margin": "md"
        })

    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "uri",
                        "label": "Google Maps 導航",
                        "uri": maps_url
                    }
                }
            ]
        }
    }

    # 有圖片才顯示，避免空網址造成錯誤
    if image_url and image_url.startswith("https://"):
        bubble["hero"] = {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover"
        }

    return bubble


# 建立可左右滑動的多景點卡片

# 建立可以分頁的景點卡片
def create_attraction_carousel(attractions, page=1):
    if not attractions:
        return None

    page_size = 10
    total_pages = (len(attractions) + page_size - 1) // page_size

    # 避免頁碼超出範圍
    page = max(1, min(page, total_pages))

    start = (page - 1) * page_size
    end = start + page_size

    # 取得目前這一頁的景點
    current_attractions = attractions[start:end]

    bubbles = [
        create_attraction_bubble(attraction)
        for attraction in current_attractions
    ]

    # 建立翻頁按鈕
    buttons = []

    if page > 1:
        buttons.append({
            "type": "button",
            "style": "secondary",
            "action": {
                "type": "postback",
                "label": "上一頁",
                "data": f"attraction_page={page - 1}"
            }
        })

    if page < total_pages:
        buttons.append({
            "type": "button",
            "style": "primary",
            "action": {
                "type": "postback",
                "label": "下一頁",
                "data": f"attraction_page={page + 1}"
            }
        })

    # 最後一張卡片放翻頁操作
    navigation_bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "繼續探索復興區",
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": f"第 {page} / {total_pages} 頁",
                    "size": "sm",
                    "color": "#888888",
                    "margin": "md"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": buttons
        }
    }

    bubbles.append(navigation_bubble)

    return {
        "type": "carousel",
        "contents": bubbles
    }
