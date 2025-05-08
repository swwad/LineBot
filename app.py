# app.py
# 這是 Line Bot 的主程式，適合 Python 初學者
# 功能：
# 1. 接收 Line 訊息（文字或圖片）
# 2. 將訊息傳送到本地 LM Studio API
# 3. 取得回應後回覆給 Line 使用者
# 4. 支援簡單的連續對話

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import requests
import os
from dotenv import load_dotenv
import csv
from datetime import datetime
import json
import base64
from db import init_db
from line_handlers import register_handlers

# 載入 .env 檔案中的環境變數
load_dotenv()

# 從環境變數取得 Line Bot 機密資料
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# LM Studio API 設定
LM_API_URL = os.getenv('LM_API_URL')
LM_MODEL_NAME = os.getenv('LM_MODEL_NAME')

# 載入提示詞設定檔
with open('prompts.json', 'r', encoding='utf-8') as f:
    PROMPTS = json.load(f)

# 初始化 Line Bot API 與 Webhook Handler
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 建立 Flask 應用程式
app = Flask(__name__)

# 用來暫存用戶對話紀錄（簡單 session 機制）
session_memory = {}

# 設定 log level（可改成 'debug' 或 'info'）
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').lower()

def log(msg, level='info'):
    if level == 'info':
        print(f"[INFO] {msg}")

@app.route("/callback", methods=['POST'])
def callback():
    # 只保留 info log，且不輸出 headers/body
    log("收到 LINE Webhook 請求", level='info')
    # 取得 X-Line-Signature 標頭
    signature = request.headers['X-Line-Signature']
    # 取得請求內容
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

if __name__ == "__main__":
    # 初始化資料庫
    init_db()
    # 註冊 LINE Bot 事件處理
    register_handlers(handler, line_bot_api, PROMPTS, LM_API_URL, LM_MODEL_NAME, session_memory)
    # 啟動 Flask 伺服器，預設監聽 5000 port
    # debug=True 方便開發時除錯
    app.run(host='0.0.0.0', port=5000, debug=True) 