# 5 號第一階段：FAQ 問答模組

此交付包只包含新增檔案，搭配你提供的 Line-Bot-main 專案使用。完成的是第一階段 FAQ，不是全部 5 號功能。尚未實作生成式 AI、中央氣象署 API、商家、交通或優惠券服務。

## 1. 放在哪裡

解壓縮後，把本包的 `modules`、`data`、`tests` 資料夾與本說明，放在原專案的 `app.py` 同一層。不要把整個 member5-faq 資料夾放在 app.py 旁邊後就直接執行；應將它裡面的檔案放進專案根目錄。

```text
Line-Bot/
├── app.py                         原有檔案
├── modules/ai_service/
│   ├── __init__.py
│   ├── __main__.py                命令列測試介面
│   ├── ai_service.py              get_reply：統一入口
│   ├── intent.py                  關鍵字意圖分類
│   └── faq.py                     FAQ 讀取、驗證與匹配
├── data/faq.json                  FAQ 內容
├── tests/test_member5_faq.py      自動測試
└── MEMBER5_README.md
```

如果團隊的 develop 已有同名檔案，先比對合併，不要直接覆蓋。本包沒有修改景點共同格式，也不包含 attractions.json。

## 2. 套件與環境變數

FAQ 只用 Python 標準函式庫，無須安裝額外套件，也不需要任何 API Key、LINE Token 或 .env。

請用 Python 3.10 以上。在 Windows 專案根目錄開啟終端機後執行下列指令。如果電腦使用 `python` 而不是 `py`，將指令開頭的 `py` 換成 `python`。

原專案的 Flask、LINE 套件只在實際接入 Bot 時需要：`py -m pip install -r requirements.txt`。現有程式讀取的 LINE 環境變數是 `CHANNEL_SECRET`、`CHANNEL_ACCESS_TOKEN`。現有 settings.py 使用 os.getenv，沒有自行載入 .env；本機測試主程式時需由啟動環境提供變數，不能只放 .env 就假設已載入。

## 3. 先獨立執行

```powershell
py -m modules.ai_service
```

可依序輸入：

| 輸入 | 預期結果 |
|---|---|
| 需要下載 App 嗎？ | 說明無須另外下載專屬 App |
| 如何分享位置？ | 說明位置訊息及目前整合狀態 |
| 這個系統可以做什麼？ | 專題介紹及功能狀態 |
| 現在是真正的 AI 嗎？ | 說明目前為關鍵字 FAQ |
| 明天會下雨嗎？ | 明確說明天氣服務尚未串接 |
| 幫我買股票 | 找不到答案的提示 |
| exit | 結束測試 |

執行自動測試：

```powershell
py -m unittest discover -s tests -p "test_member5_*.py" -v
```

交付時 13 項測試通過。沒有執行真實 LINE Webhook、回覆 API 或 Vercel 部署測試。

## 4. 給 1 號的接入方式

公開介面：

```python
from modules.ai_service import get_reply

reply_text = get_reply("需要下載 App 嗎？")
```

輸入必須為字串，回傳為答案字串。函式不呼叫 LINE API、不持有 reply_token，不建立使用者狀態。FAQ 資料每次查詢重新讀取，修改 JSON 後下次查詢即可使用。

### 必要串接：handlers/message_handler.py

原因：目前未知文字會原樣回覆，必須改成呼叫 FAQ 才能在 LINE 收到答案。此檔案屬於 1 號，因此本包提供明確修改片段，由整合時套用。

在頂端新增：

```python
from modules.ai_service import get_reply
```

保留既有 postback、附近景點推薦、景點導覽、泰雅文化分支。將原本最後的 AI 問答與 else 區塊改成：

```python
        elif text == 'AI 問答':
            reply_text = get_reply(text)

        else:
            reply_text = get_reply(text)
```

後面的 `line_bot_api.reply_message(...)` 保持原樣，統一回覆一次。不要在 FAQ 模組內再次回覆 LINE。未來其他模組的文字路由應放在最後 else 之前。

### 可選串接：handlers/postback_handler.py

原因：讓 Rich Menu 的 AI 按鈕顯示目前真正可用的功能。頂端加入同樣的 import，並將 menu_ai 分支改成：

```python
    elif data == 'menu_ai':
        reply_text = get_reply('AI 問答')
```

不需修改 app.py、config/settings.py、requirements.txt。

### LINE 整合驗收

1. 由 1 號在測試環境套用串接修改。
2. 傳送「需要下載 App 嗎？」確認收到 FAQ 答案，而非原文。
3. 點 AI 問答選單，確認顯示 FAQ 引導。
4. 傳送「景點導覽」「泰雅文化」「附近景點推薦」，確認仍走各自原有分支。
5. 確認每個事件只回覆一次。

## 5. 新增 FAQ

data/faq.json 是獨立 FAQ 格式，不會改動景點資料格式。每筆需要唯一字串 id、question、keywords 陣列、answer。請維持合法 JSON，答案限制 2000 字以內。

先比對完整問題；未完全符合時，採用最長匹配關鍵字。同分且答案不同時不隨機選答案，會進入分類提示或找不到答案的流程。這不是語意理解，不能保證識別所有問法、否定句或多問題；請透過測試補充具體關鍵字，避免只用「我」「怎麼」等過於籠統詞語。

尚未接入的服務會回覆未完成提示。未來真正串接後，需更新 ai_service.py 的 PENDING 以及 FAQ 中對應的狀態說明。景點問答應使用 2 號提供、經確認的 attractions.json；不要把企劃中的示例座標、時間或電話當成真實資料。

## 6. Git 提交

你下載的 ZIP 沒有 .git，也不含分支歷史。正式提交前，請先使用 Git clone 或 GitHub Desktop 取得團隊 repo，再以最新 develop 建立或切換到 feature-ai-service；若分支已存在，沿用該分支。將本包新增檔案合入該工作目錄後提交。

確認目前分支：

```powershell
git branch --show-current
```

應顯示 `feature-ai-service`。然後測試並提交：

```powershell
py -m unittest discover -s tests -p "test_member5_*.py" -v
git add modules/ai_service data/faq.json tests/test_member5_faq.py MEMBER5_README.md
git commit -m "feat: 新增可獨立測試的 FAQ 問答模組"
git push -u origin feature-ai-service
```

在 GitHub 建立 feature-ai-service → develop 的 Pull Request。此交付沒有幫你建立 Git 分支、commit、push 或部署。handlers 的串接若另行套用，請在審查差異後另外加入提交。

## 7. 後續開發

先完成本版的 LINE 整合驗收，再串接天氣 API；之後依團隊需求處理景點資料問答、商家資料，以及 AI API。AI 供應商、費用與資料來源尚未決定，本版不預先綁定。
