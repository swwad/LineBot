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

# 記錄對話到 CSV 檔案
def log_to_csv(user_id, user_content, reply_content, msg_type):
    # 設定 CSV 檔案名稱
    csv_file = 'chat_log.csv'
    # 取得現在時間
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 準備要寫入的資料
    row = [now, user_id, msg_type, user_content, reply_content]
    # 如果檔案不存在，先寫入標題
    write_header = not os.path.exists(csv_file)
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(['時間', '用戶ID', '訊息型態', '用戶內容', '回覆內容'])
        writer.writerow(row)

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

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    user_text = event.message.text
    # 新增：判斷是否為清除指令（從 PROMPTS 讀取，缺漏直接報錯）
    reset_cmds = PROMPTS["reset_cmds"]
    reset_reply = PROMPTS["reset_reply"]
    if user_text.strip() in reset_cmds:
        session_memory.pop(user_id, None)
        reply_text = reset_reply
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        log_to_csv(user_id, user_text, reply_text, '文字')
        log(f"用戶 {user_id}：{user_text} → {reply_text}", level='info')
        return
    # 取得用戶過去對話（如果有）
    history = session_memory.get(user_id, [])
    # 準備 messages，最前面加上 system prompt，並嚴格要求繁體中文（從 PROMPTS 讀取，缺漏直接報錯）
    system_prompt = PROMPTS["text"] + PROMPTS["zh_tw_force"]
    user_prompt_suffix = PROMPTS["zh_tw_user_suffix"]
    messages = [{"role": "system", "content": system_prompt}] + history
    messages.append({"role": "user", "content": user_text + user_prompt_suffix})
    # 呼叫 LM Studio API
    response = requests.post(
        LM_API_URL,
        json={
            "model": LM_MODEL_NAME,  # 指定模型名稱
            "messages": messages,
            "stream": False  # 關閉串流，簡化回應
        }
    )
    if response.status_code == 200:
        result = response.json()
        # 取得模型回應內容
        reply_text = result['choices'][0]['message']['content']
        # 新增本次 user/assistant 對話到 history
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply_text})
        # 更新 session
        session_memory[user_id] = history[-10:]  # 只保留最近 10 則
    else:
        reply_text = PROMPTS['api_error']
    # 回覆用戶
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    # 記錄對話到 CSV
    log_to_csv(user_id, user_text, reply_text, '文字')
    log(f"用戶 {user_id}：{user_text} → {reply_text}", level='info')

# 處理圖片訊息事件
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    # 取得圖片內容
    message_content = line_bot_api.get_message_content(event.message.id)
    # 產生以 user_id 與時間為名的檔案名稱，並存放於 upload/image/userid/
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_dir = os.path.join('upload', 'image', user_id)
    os.makedirs(save_dir, exist_ok=True)
    temp_file_path = os.path.join(save_dir, f"{now_str}.jpg")
    with open(temp_file_path, 'wb') as f:
        for chunk in message_content.iter_content():
            f.write(chunk)
    # 將圖片轉為 base64 並組成 data url
    with open(temp_file_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    img_data_url = f"data:image/jpeg;base64,{img_b64}"
    # 組成 messages，system prompt 與 user prompt 皆從 prompts.json 讀取，缺漏直接報錯
    system_prompt = PROMPTS["image"] + PROMPTS["zh_tw_force"]
    image_user_prompt = PROMPTS["image_user"]
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": image_user_prompt},
                {"type": "image_url", "image_url": {"url": img_data_url}}
            ]
        }
    ]
    # 組成 payload
    payload = {
        "model": LM_MODEL_NAME,
        "messages": messages,
        "temperature": 0.7
    }
    # 發送 POST 請求
    response = requests.post(LM_API_URL, json=payload)
    if response.status_code == 200:
        result = response.json()
        # 依照你的 API 回傳格式取得內容
        reply_text = result.get('choices', [{}])[0].get('message', {}).get('content', PROMPTS['image_success'])
    else:
        reply_text = PROMPTS['image_error']
    # 回覆用戶
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    # 記錄對話到 CSV
    log_to_csv(user_id, temp_file_path, reply_text, '圖片')
    log(f"用戶 {user_id} 上傳圖片（{temp_file_path}） → {reply_text}", level='info')

if __name__ == "__main__":
    # 啟動 Flask 伺服器，預設監聽 5000 port
    # debug=True 方便開發時除錯
    app.run(host='0.0.0.0', port=5000, debug=True) 