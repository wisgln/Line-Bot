# Gemini 本機對話測試

在 .env 加入以下設定，不要提交金鑰：

```dotenv
OPENAI_ENABLED=false
GEMINI_ENABLED=true
GEMINI_API_KEY=自己的金鑰
GEMINI_MODEL=gemini-3.8-flash
```

Google 專案需保持 Free tier；程式無法判定帳戶是否開啟付費。
免費額度以 AI Studio 顯示為準。超額不重試、不切換其他供應商。
程式不會啟用 Google 帳單，也不會呼叫原 OpenAI 模組。

執行 `py -m modules.ai_service`。依序輸入：
1. 我們有老人小孩，幫我排復興一日行程，推薦餐廳住宿
2. 從桃園出發，開車，不想走太多路，當天回家
3. 午餐換便宜一點，其他條件保留
4. 清除對話

每次 API 請求送出公開商家、農特產、FAQ 與該對話最近8輪文字；不送 LINE 使用者識別碼。
記憶僅存伺服器程序記憶體，最多100個對話，閒置30分鐘清除；重啟即消失。
長對話舊條件可能被截斷，應再次確認。這不是正式的多伺服器持久化方案。
LINE handler 已傳入每人每聊天室獨立的 session_id；正式部署需1號整合共用儲存與重送去重。
部署平台需設定環境變數；只有 CLI 會讀取本機 .env。

現有資料沒有驗證景點、無障礙設施與車程，因此 AI 只能提供行程草案、商家選擇及追問。
不能據此保證輪椅適用、空房、即時價格或路況。正式完整行程還需景點與交通資料整合。
本次自動化測試使用模擬回應，不代表真實模型回答品質已驗收。

官方文件：https://ai.google.dev/gemini-api/docs/pricing
