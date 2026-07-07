
import time
from urllib.parse import urlparse

import requests as requests_lib


CAPTCHA_API_KEY = input("2CAPTCHA_API_KEY: ")
PROXY_URL = input("PROXY: ")

USER_AGENT = "28,1023,androidPhoneApp,1600x900,1.5,Redmi,23113RKC6C,7f2821773c5c1659,1783364599220"

CAPTCHA_SITE_KEY = "ysc1_fCg9cqGdvGHetWnniD6z0glqM0gvjnhRDzxsSke8e4d2b52b" 
CAPTCHA_PAGE_URL = "https://youdo.com/web-view-signin?authProviders=SOCIAL_VK_ENABLED,SOCIAL_OK_ENABLED,SOCIAL_MAIL_ENABLED,SOCIAL_GOOGLE_ENABLED,PROMO_CODE_INPUT_AUTH_ENABLED"


requests = requests_lib.Session()
requests.proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL
}


def parse_proxy_url(proxy_url: str) -> dict:
    if "://" not in proxy_url:
        proxy_url = "http://" + proxy_url

    parsed = urlparse(proxy_url)

    return {
        "proxyType": parsed.scheme,
        "proxyAddress": parsed.hostname,
        "proxyPort": parsed.port,
        "proxyLogin": parsed.username,
        "proxyPassword": parsed.password
    }


def get_smartcaptcha_token():
    create_task_url = "https://api.2captcha.com/createTask"
    
    proxy_parts = parse_proxy_url(PROXY_URL)

    create_task_url = "https://api.2captcha.com/createTask"
    payload = {
        "clientKey": CAPTCHA_API_KEY,
        "task": {
            "type": "YandexSmartCaptchaTask", 
            "websiteURL": CAPTCHA_PAGE_URL,
            "websiteKey": CAPTCHA_SITE_KEY,
            "userAgent": USER_AGENT,
            **proxy_parts
        }
    }

    response = requests.post(create_task_url, json=payload)
    
    response_data = response.json()
    if response_data.get("errorId") != 0:
        raise RuntimeError(f"Ошибка создания задачи: {response_data}")
        
    task_id = response_data["taskId"]
    print(f"[*] Задача {task_id} создана. Ожидаем решения...")

    get_result_url = "https://api.2captcha.com/getTaskResult"
    result_payload = {
        "clientKey": CAPTCHA_API_KEY,
        "taskId": task_id
    }

    while True:
        time.sleep(5)
        res = requests.post(get_result_url, json=result_payload).json()
        
        if res.get("errorId") != 0:
            raise RuntimeError(f"Ошибка при получении результата: {res}")
            
        if res.get("status") == "ready":
            captcha_token = res["solution"]["token"]
            print("[+] Капча успешно решена.")
            return captcha_token
        else:
            print("[*] Решение еще не готово, ожидаем...")


def main():
    print("Captcha token: ", get_smartcaptcha_token())

if __name__ == "__main__":
    main()
