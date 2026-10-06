# 5 號：FAQ 與復興區天氣查詢模組

目前已完成關鍵字 FAQ，以及中央氣象署桃園市復興區天氣預報查詢，並提供統一入口 `get_reply(text)`。

已在本機成功取得氣象署預報，FAQ 與天氣路由的 15 項自動測試全部通過。尚未完成 LINE 實際收發整合驗收。

尚未實作生成式 AI、商家、交通或優惠券服務。

## 1. 檔案位置

所有指令都在專案根目錄，也就是 app.py 所在資料夾執行。

```text
Line-Bot/
├── app.py
├── modules/
│   ├── ai_service/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── ai_service.py
│   │   ├── intent.py
│   │   └── faq.py
│   └── weather/
│       └── weather_service.py
├── data/
│   └── faq.json
├── tests/
│   └── test_member5_faq.py
├── .env                 本機設定，不提交 Git
├── .env.example         設定範例，不放真實授權碼
├── requirements.txt
└── MEMBER5_README.md
```

本次未修改 app.py、handlers 或景點共同資料格式。LINE 串接由 1 號整合時處理。

## 2. 環境與套件

使用 Python 3.10 以上，目前本機測試環境為 Python 3.14.8。

只執行 FAQ 問答不需要 API 授權碼。天氣功能需要：

- requests：發送氣象署 API 請求
- python-dotenv：讀取本機 .env
- truststore：使用系統憑證驗證 HTTPS 連線

只測試這兩個模組，可先安裝：

```powershell
py -m pip install "requests>=2.32.3" python-dotenv truststore
```

整合完整專案時，依 requirements.txt 安裝：

```powershell
py -m pip install -r requirements.txt
```

天氣模組使用 Requests 的自訂連線介面，需要 requests 2.32.3 以上。

## 3. 天氣授權碼

在專案根目錄的 .env 設定：

```dotenv
WEATHER_API_KEY=請填入自己的氣象署授權碼
```

請將等號後面的範例文字替換成真正授權碼。

- 不要把 .env 或真實授權碼提交到 GitHub。
- .env.example 只保留變數名稱與空值或範例。
- 部署環境需另外設定 WEATHER_API_KEY。
- 天氣模組會讀取專案根目錄的 .env，且不覆蓋已存在的環境變數。

天氣模組載入 .env 不代表 LINE 主程式的啟動設定已完成。LINE 所需的 CHANNEL_SECRET、CHANNEL_ACCESS_TOKEN 仍由整合端設定。

## 4. 本機執行

### FAQ 與天氣統一入口

```powershell
py -m modules.ai_service
```

可輸入：

| 輸入 | 預期結果 |
|---|---|
| 需要下載 App 嗎？ | 說明無須另外下載專屬 App |
| 如何分享位置？ | FAQ 中的位置分享說明 |
| 復興區天氣如何？ | 桃園市復興區近期天氣預報 |
| 使用說明 | 顯示可用功能引導 |
| 幫我買股票 | 找不到答案的提示 |
| exit | 結束命令列測試 |

也可以直接測試統一入口：

```powershell
py -c "from modules.ai_service import get_reply; print(get_reply('復興區天氣如何？'))"
```

### 單獨測試天氣

```powershell
py -m modules.weather.weather_service
```

此指令會實際連線氣象署，需要網路與有效授權碼。

## 5. 天氣功能範圍

資料來源：中央氣象署氣象資料開放平臺。

使用資料集 F-D0047-005，從桃園市鄉鎮預報中選取復興區。

目前回覆內容：

- 尚未結束的預報時段，最多三筆
- 氣象署提供的天氣描述
- 台灣時間的查詢時間
- 資料來源及「預報，非即時觀測」說明

目前固定查詢桃園市復興區，尚不支援指定其他地區或依問題選取特定日期。即使輸入「明天會下雨嗎」，目前仍回傳近期時段，不保證只包含明天。

HTTPS 連線透過 SystemTLSAdapter 使用 truststore 的系統憑證驗證，沒有關閉憑證檢查，也沒有全域替換其他模組的 SSL 設定。

## 6. 自動測試與驗證範圍

執行：

```powershell
py -m unittest discover -s tests -p "test_member5_faq.py" -v
```

目前結果：15 項測試全部通過。

包含 FAQ 匹配、文字正規化、資料錯誤處理、意圖分類，以及：

- 天氣問題會呼叫天氣模組並回傳其結果
- 一般 FAQ 不會呼叫天氣模組

自動測試中的天氣回覆使用模擬資料，不會連線氣象署；執行這份測試仍需安裝天氣模組的套件。

另外已手動驗證：
- 單獨執行天氣模組可取得真實預報
- 透過 get_reply() 可取得真實預報
- 原本 FAQ 問題仍能回答

這 15 項測試尚未涵蓋天氣資料解析與所有連線錯誤情境，也不代表已通過 LINE 或部署環境的整合驗收。

## 7. 給 1 號的接入介面

```python
from modules.ai_service import get_reply

reply_text = get_reply("需要下載 App 嗎？")
reply_text = get_reply("復興區天氣如何？")
```

輸入為字串，回傳為回答字串。

get_reply() 不呼叫 LINE API、不持有 reply_token，也不建立使用者狀態。LINE 回覆由整合端統一處理。

處理順序：
1. 使用說明與輸入長度檢查
2. FAQ 匹配
3. 意圖分類
4. 天氣查詢，或其他服務的未完成提示

天氣查詢是同步網路請求，會等待氣象署回應；整合時需評估 Webhook 的處理時間及逾時行為。

### 文字訊息處理

由 1 號依最新 handlers/message_handler.py 合併以下邏輯。

新增 import：

```python
from modules.ai_service import get_reply
```

保留附近景點、景點導覽、泰雅文化等既有路由。AI 問答及最後未匹配的文字，可交給：

```python
reply_text = get_reply(text)
```

原有 LINE 回覆程式統一發送一次，不要在模組內重複回覆。

### AI 選單

若仍使用 menu_ai 作為 postback 值，可呼叫：

```python
reply_text = get_reply("AI 問答")
```

### LINE 整合驗收

1. 在測試環境安裝套件並設定環境變數。
2. 傳送 FAQ 問題，確認收到答案。
3. 傳送「復興區天氣如何？」，確認收到復興區預報。
4. 點擊 AI 問答選單，確認顯示功能引導。
5. 確認景點、文化及附近推薦仍走原有路由。
6. 確認每個事件只回覆一次。
7. 驗證授權失敗、連線逾時時的使用者提示。

## 8. FAQ 維護

data/faq.json 使用獨立格式，不修改景點資料格式。

每筆包含：
- 唯一 id
- question
- keywords 陣列
- answer

先比對完整問題，再採用最長匹配關鍵字。同分且答案不同時，不隨機選答案。

目前是關鍵字分類，不具備生成式 AI 的語意理解能力，不能保證識別所有問法、否定句或多個問題。

功能更新時，也要同步更新 FAQ 中的功能狀態描述。

## 9. Git 與交接

目前使用 feature-ai-service 分支，已有合併至 develop 的 PR：

https://github.com/wisgln/Line-Bot/pull/1

後續修改提交並推送至同一分支後，會更新尚未合併的 PR。合併前由團隊確認最新狀態及差異。

提交前確認：
- 測試通過
- .env 未加入版本控制
- 差異沒有真實授權碼
- requirements.txt 與功能說明同步更新

## 10. 待完成

- 檢查 data/faq.json 是否仍有「天氣尚未串接」的舊說明。
- 補齊天氣資料解析與錯誤情境的自動測試。
- 由 1 號完成 LINE 串接及實際收發驗收。
- 依團隊需求再開發商家、交通、優惠券或生成式 AI。
