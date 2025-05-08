import requests

def call_lm_api(messages, model_name, api_url):
    """
    呼叫 LM Studio API 並回傳回應內容（純文字訊息）
    :param messages: list of dict
    :param model_name: str
    :param api_url: str
    :return: str (回應文字)
    """
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False
    }
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        return None

def call_lm_api_with_image(messages, model_name, api_url, temperature=0.7):
    """
    呼叫 LM Studio API 並回傳回應內容（圖片訊息）
    :param messages: list of dict
    :param model_name: str
    :param api_url: str
    :param temperature: float
    :return: str (回應文字)
    """
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature
    }
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result.get('choices', [{}])[0].get('message', {}).get('content')
    else:
        return None 