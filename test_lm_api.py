# test_lm_api.py
# 這個檔案用來測試呼叫 LM Studio API 並將回應輸出到 Console
# 適合 Python 初學者，結構清楚、易於擴充

import os
import requests
from dotenv import load_dotenv

# 1. 載入 .env 檔案，取得 API 設定
load_dotenv()
LM_API_URL = os.getenv('LM_API_URL')
LM_MODEL_NAME = os.getenv('LM_MODEL_NAME')

# 2. 封裝 API 呼叫成一個函式，方便重複測試不同訊息
def call_lm_api(messages):
    """
    呼叫 LM Studio API 並回傳回應內容
    :param messages: 對話歷史（list of dict）
    :return: 回應文字（str）
    """
    payload = {
        "model": LM_MODEL_NAME,
        "messages": messages,
        "stream": False
    }
    response = requests.post(LM_API_URL, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        print(f"API 呼叫失敗，狀態碼：{response.status_code}")
        print(response.text)
        return None

# 3. 定義多個測試案例
def test_simple_intro():
    """測試：請模型自我介紹"""
    messages = [{"role": "user", "content": "你好，請簡單自我介紹。"}]
    reply = call_lm_api(messages)
    print("【自我介紹測試】\n", reply)

def test_math_question():
    """測試：數學問題"""
    messages = [{"role": "user", "content": "1+1等於多少？"}]
    reply = call_lm_api(messages)
    print("【數學問題測試】\n", reply)

def test_context_conversation():
    """測試：連續對話"""
    messages = [
        {"role": "user", "content": "你是誰？"},
        {"role": "assistant", "content": "我是AI助理。"},
        {"role": "user", "content": "你可以幫我做什麼？"}
    ]
    reply = call_lm_api(messages)
    print("【連續對話測試】\n", reply)

# 4. 主程式區塊，執行所有測試案例
if __name__ == "__main__":
    print("===== LM Studio API 單元測試開始 =====")
    test_simple_intro()
    test_math_question()
    test_context_conversation()
    print("===== 測試結束 =====") 