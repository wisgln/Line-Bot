# OpenAI 旅遊問答

既有 FAQ、天氣、商家、農產、緊急及交通規則優先；只有未命中的問題才呼叫 OpenAI。
這不是即時上網查詢，也不保存多輪對話。AI 仍可能回答錯誤，需在正式部署前驗收。

## 本機設定

在專案 `.env` 自行加入（不要將金鑰貼到聊天或提交 Git）：

```dotenv
OPENAI_ENABLED=true
OPENAI_API_KEY=你的OpenAI_API金鑰
OPENAI_MODEL=gpt-4.1-mini
```

互動測試入口會讀取專案 `.env`：

```powershell
py -m modules.ai_service
```

試問「幫我規劃復興兩天一夜，先問我需要哪些資訊」。看到「✨ AI 旅遊小幫手」才是成功取得生成回覆。
輸入 exit 離開。只有規則式答案或原本找不到答案提示，可能是未啟用、缺少金鑰、API 錯誤或連線逾時。
一般 `py -c` 不會由此模組自動載入 `.env`；需要先載入 dotenv 或設定環境變數。

## 部署與費用

由整合者在部署平台設定以上環境變數並重新部署。API 使用需有可用額度，依 OpenAI 帳戶計費。
啟用後，未命中的問題文字與專案公開 FAQ／商家／農產 JSON 會送至 OpenAI；不傳送 LINE 使用者 ID。
設定 `store=false`，不是零資料保留保證。未使用上網工具或即時庫存。
目前每次請求最多1200輸出tokens，15秒逾時、無自動重試；這不是帳戶總費用上限。
停用請設 `OPENAI_ENABLED=false`。正式公開前請設定平台用量控制並做實際問答驗收。

## 驗證

自動測試使用模擬回應，不連線、不計費：
`py -m unittest discover -s tests -p "test_member5_*.py" -v`

官方文件：https://developers.openai.com/api/docs/quickstart
