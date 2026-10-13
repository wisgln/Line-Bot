# 活動自動更新

資料來源：https://travel.tycg.gov.tw/open-api
規格：https://travel.tycg.gov.tw/open-api/swagger/ui/index

每天台灣時間 08:17 由 GitHub Actions 下載今年及明年的官方觀光行事曆。
排程可能延遲，不代表即時查詢。無須 Gemini 或其他 API 金鑰。

## 資料範圍

- 保留 `data/events.json` 手動資料，不會自動刷新它的查閱日期。
- 自動下載資料存入 `data/events_auto.json`，查詢及 AI 共用同一份活動資料。
- 官方 API 沒有行政區欄位，目前保守篩選標題含「復興區、角板山、小烏來、拉拉山、宇內溪、雪霧鬧」的公告。因此並非復興所有活動；其他官方來源仍可手動補充。
- 排除日期待定及已結束的活動；公告區間不保證每日有場次。場地、取消異動及預約請查官方頁面。
- 完整分頁下載、格式驗證全部通過才覆寫。失敗退出並保留舊檔；GitHub Actions 會顯示失敗。超過 30 天沒有成功查閱的資料不再推薦。
- 成功取得完整但沒有符合活動的清單時，自動檔會清空；手動檔仍保留。

## 啟用（交給負責整合的組員）

1. 合併本功能及工作流程到 GitHub **預設分支**；只放功能分支不會啟用每日排程。
2. 確認允許 GitHub Actions 執行及 contents 寫入；受保護分支若禁止 bot 推送，請管理員採用符合專案政策的資料更新流程，不要關閉保護。
3. Actions → Update official events → Run workflow，檢查成功及資料提交。
4. 確認 LINE 部署使用相同分支且會取得該次資料更新。GitHub 更新不等於 Vercel 已更新；用目前部署流程驗證重新部署後的活動回覆。若部署是另一個 GitHub workflow，由 GITHUB_TOKEN 推送通常不會觸發它，需由整合組員另外接部署步驟。
5. 公開儲存庫長期無活動可能停用排程，管理者應查看 Actions 狀態。GitHub Actions 使用量依帳戶方案計算。

## 本機檢查

```powershell
py scripts/update_events.py
py -m unittest discover -s tests -p "test_member5_*.py" -v
```

下載程式只寫自動資料檔，不會改 `.env` 或自行提交到 GitHub。
