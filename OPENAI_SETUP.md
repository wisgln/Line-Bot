# OpenAI 旅遊問答與行程規劃

既有 FAQ、天氣、商家、農產、緊急及交通規則優先；行程規劃、修改與未命中的旅遊問題由 OpenAI 處理。
這不是即時上網查詢。對話及行程記憶只保留在應用程式的短期記憶中，不寫入資料庫。AI 仍可能回答錯誤，需在正式部署前驗收。

## 本機設定

在專案 `.env` 自行加入（不要將金鑰貼到聊天或提交 Git）：

```dotenv
OPENAI_ENABLED=true
OPENAI_API_KEY=你的OpenAI_API金鑰
OPENAI_MODEL=gpt-4.1-mini
GROQ_ENABLED=false
GEMINI_ENABLED=false
```

互動測試入口會讀取專案 `.env`：

```powershell
python -m modules.ai_service
```

試問「幫我規劃復興兩天一夜，先問我需要哪些資訊」。能繼續補充交通、同行者與步行限制，並產生通過系統驗證的行程站點，才代表主要 OpenAI 路由正常。
輸入 exit 離開。只有規則式答案或原本找不到答案提示，可能是未啟用、缺少金鑰、API 錯誤或連線逾時。
一般 `py -c` 不會由此模組自動載入 `.env`；需要先載入 dotenv 或設定環境變數。

## 部署與費用

由整合者在部署平台設定以上環境變數並重新部署。API 使用需有可用額度，依 OpenAI 帳戶計費。
啟用後，旅遊問題、短期對話歷史與專案公開景點／FAQ／商家／農產 JSON 會送至 OpenAI；不傳送 LINE 使用者 ID。
設定 `store=false`，不是零資料保留保證。未使用上網工具或即時庫存。
目前每次請求最多1200輸出 tokens，30秒逾時、無自動重試；這不是帳戶總費用上限。
停用請設 `OPENAI_ENABLED=false`。正式公開前請設定平台用量控制並做實際問答驗收。

## 驗證

自動測試使用模擬回應，不連線、不計費：
`python -m pytest -q`

官方文件：https://developers.openai.com/api/docs/quickstart
