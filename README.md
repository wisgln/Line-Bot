# 文藝復興之旅－復興區智慧觀光導覽 LINE Bot

桃園市復興區 × 泰雅族文化 × 智慧行動科技

透過 LINE Bot，讓使用者不需下載額外 App，加好友即可取得景點資訊、在地商家、泰雅文化內容、AI 智慧問答、個人化行程推薦、天氣與交通資訊等服務。

---

## 核心功能

1. 智慧 AI 互動諮詢
2. 在地觀光資源整合
3. 個人化行程規劃
4. 泰雅文化保存與數位推廣

## 技術架構

- **展示層**：LINE Bot / Rich Menu / Flex Message / Carousel / Quick Reply
- **通訊層**：LINE Messaging API / Webhook
- **後端**：Python（Flask）
- **資料與外部服務**：MySQL / MongoDB、Google Maps API、中央氣象署 API、AI API
- **部署**：Vercel

---

## 專案結構

## 專案結構

```
fuxing-linebot/
├── app.py                  # 主入口，webhook 路由與事件註冊
├── config/
│   └── settings.py         # 環境變數集中管理
├── handlers/
│   ├── message_handler.py  # 文字訊息處理
│   ├── location_handler.py # 定位訊息處理
│   └── postback_handler.py # postback 事件處理
├── modules/                # 各功能模組（依負責人分工）
│   ├── attraction/
│   ├── location/
│   ├── culture/
│   ├── ai_service/
│   ├── weather/
│   └── merchant/
├── data/                    # JSON 資料（景點、文化、商家、FAQ）
├── templates/flex/          # Flex Message 樣板
├── .env.example              # 環境變數範本（不含實際金鑰）
└── .gitignore
```


---

## 五人分工

| 編號 | 負責項目 | 對應資料夾 |
|---|---|---|
| 1 號 | 系統核心與整合、部署、GitHub 管理 | `app.py`, `config/`, `handlers/` |
| 2 號 | 景點導覽模組 | `modules/attraction/` |
| 3 號 | LBS 定位與智慧推薦 | `modules/location/` |
| 4 號 | 泰雅文化與互動 | `modules/culture/` |
| 5 號 | AI 與旅遊生活服務 | `modules/ai_service/`, `modules/weather/`, `modules/merchant/` |

---

## 景點共同資料格式

所有模組共用同一份 `attractions.json` 格式，**請勿自行更改格式**：

```json
{
    "id": 1,
    "name": "小烏來天空步道",
    "category": "自然景觀",
    "latitude": 24.0000,
    "longitude": 121.0000,
    "address": "桃園市復興區...",
    "opening_hours": "08:00-17:00",
    "phone": "03-xxxxxxx",
    "description": "景點介紹",
    "image_url": "https://...",
    "maps_url": "https://maps.google.com/..."
}
```

---

## Git 開發流程

分支架構：

main → 穩定、可展示版本
develop → 五人功能整合測試
feature-xxx → 各自開發分支


開發步驟：

```bash
# 開始工作前，先同步 develop
git checkout develop
git pull

# 切回自己的分支開發
git checkout feature-你的模組名稱

# 開發完成後
git add .
git commit -m "feat: 完成功能名稱"
git push
```

推上去後到 GitHub 建立 Pull Request，**先合併進 `develop`**，測試沒問題後才會合併進 `main`。**請勿直接 push 到 main。**

---

## 環境變數設定

複製 `.env.example` 為 `.env`，並填入以下變數：
```
CHANNEL_ACCESS_TOKEN=
CHANNEL_SECRET=
WEATHER_API_KEY=
GOOGLE_MAPS_API_KEY=
AI_API_KEY=
```

`.env` 已加入 `.gitignore`，不會被上傳，請勿把金鑰直接寫死在程式碼裡。

---

## 開發原則

- 不把所有功能寫在 `app.py`，優先模組化
- 優先修改自己負責的資料夾，若需修改他人檔案請先說明原因
- 不隨意更改共同資料格式（尤其是景點 JSON 格式）
- 每完成一個小功能就 commit，不要等全部做完才第一次 merge
- 確保自己的功能可以被其他模組 import 使用