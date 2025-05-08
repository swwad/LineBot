from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import requests
import os
import base64
from db import log_to_db
from lm_api import call_lm_api, call_lm_api_with_image

# 這些變數與 handler 需由 app.py 傳入
PROMPTS = None
LM_API_URL = None
LM_MODEL_NAME = None
line_bot_api = None
handler = None
session_memory = None

def register_handlers(_handler, _line_bot_api, _PROMPTS, _LM_API_URL, _LM_MODEL_NAME, _session_memory):
    global handler, line_bot_api, PROMPTS, LM_API_URL, LM_MODEL_NAME, session_memory
    handler = _handler
    line_bot_api = _line_bot_api
    PROMPTS = _PROMPTS
    LM_API_URL = _LM_API_URL
    LM_MODEL_NAME = _LM_MODEL_NAME
    session_memory = _session_memory

    @handler.add(MessageEvent, message=TextMessage)
    def handle_text_message(event):
        user_id = event.source.user_id
        user_text = event.message.text
        reset_cmds = PROMPTS["reset_cmds"]
        reset_reply = PROMPTS["reset_reply"]
        if user_text.strip().lower() in [cmd.lower() for cmd in reset_cmds]:
            session_memory.pop(user_id, None)
            reply_text = reset_reply
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
            log_to_db(user_id, user_text, reply_text, '文字')
            return
        history = session_memory.get(user_id, [])
        system_prompt = PROMPTS["text"] + PROMPTS["zh_tw_force"]
        user_prompt_suffix = PROMPTS["zh_tw_user_suffix"]
        messages = [{"role": "system", "content": system_prompt}] + history
        messages.append({"role": "user", "content": user_text + user_prompt_suffix})
        reply_text = call_lm_api(messages, LM_MODEL_NAME, LM_API_URL)
        if reply_text is not None:
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": reply_text})
            session_memory[user_id] = history[-10:]
        else:
            reply_text = PROMPTS['api_error']
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        log_to_db(user_id, user_text, reply_text, '文字')

    @handler.add(MessageEvent, message=ImageMessage)
    def handle_image_message(event):
        user_id = event.source.user_id
        message_content = line_bot_api.get_message_content(event.message.id)
        from datetime import datetime
        now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join('upload', 'image', user_id)
        os.makedirs(save_dir, exist_ok=True)
        temp_file_path = os.path.join(save_dir, f"{now_str}.jpg")
        with open(temp_file_path, 'wb') as f:
            for chunk in message_content.iter_content():
                f.write(chunk)
        with open(temp_file_path, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode()
        img_data_url = f"data:image/jpeg;base64,{img_b64}"
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
        payload = {
            "model": LM_MODEL_NAME,
            "messages": messages,
            "temperature": 0.7
        }
        reply_text = call_lm_api_with_image(messages, LM_MODEL_NAME, LM_API_URL, temperature=0.7)
        if reply_text is None:
            reply_text = PROMPTS['image_error']
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        log_to_db(user_id, temp_file_path, reply_text, '圖片') 