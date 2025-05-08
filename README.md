# LineBot 多模態助理

本專案是一個支援多模態（文字+圖片）對話的 LINE Bot，整合本地 LM Studio API，所有提示詞皆集中於 `prompts.json` 管理，並採用模組化結構方便擴充。

## 主要功能
- 支援 LINE 文字與圖片訊息
- 圖片自動存放於 `upload/image/用戶ID/`
- 所有提示詞、指令、語言要求、錯誤訊息皆集中於 `prompts.json`
- 對話紀錄自動記錄於 SQLite 資料庫 `chat_log.db`
- 程式碼高度模組化，方便擴充與維護

## 專案結構說明
- `app.py`：主程式入口，負責初始化、載入設定、啟動伺服器
- `db.py`：資料庫操作（初始化、寫入對話紀錄）
- `line_handlers.py`：LINE Bot 事件處理（文字、圖片訊息）
- `lm_api.py`：呼叫 LM Studio API（可自行擴充或更換 API）
- `prompts.json`：所有提示詞、指令、錯誤訊息集中管理

## 安裝步驟

1. 複製本專案
2. 安裝 Python 依賴
   ```bash
   pip install -r requirements.txt
   ```
3. 設定 `.env` 檔案（參考 `.env.example`）
4. 啟動
   ```bash
   python app.py
   ```

## prompts.json 範例
```json
{
  "text": "你是一個親切且專業的中文助理，請用簡潔明瞭的方式回答用戶的問題。",
  "image": "你是一個圖像辨識專家，請根據圖片內容給出詳細的中文說明。",
  "zh_tw_force": "請務必用繁體中文回答。",
  "zh_tw_user_suffix": "（請用繁體中文回答）",
  "image_user": "請描述這張圖：（請用繁體中文回答）",
  "reset_cmds": ["清除對話", "/reset", "reset", "清空對話"],
  "reset_reply": "已清除對話紀錄！",
  "api_error": "LM Studio API 發生錯誤，請稍後再試。",
  "image_error": "LM Studio API 圖片辨識失敗。",
  "image_success": "圖片辨識成功，但未取得內容。"
}
```

## 注意事項
- 請勿將 `.env`、`upload/`、`chat_log.db` 等敏感或大量檔案加入版本控制
- 所有提示詞請於 `prompts.json` 管理
- 若要擴充或更換 API，只需修改 `lm_api.py`，不需動到主程式

## License
MIT 