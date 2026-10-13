
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
def create_attraction_carousel(attractions):
    if not attractions:
        return None

    bubbles = [
        create_attraction_bubble(attraction)
        for attraction in attractions[:12]
    ]

    return {
        "type": "carousel",
        "contents": bubbles
    }
