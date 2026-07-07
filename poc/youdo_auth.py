"""
Логин в YouDo по телефону + привязка FCM push-токена к аккаунту.
"""
import os
import time
import uuid

import requests

from youdo_request_sign import generate_signature_headers


ROOT_HOST = "https://youdo.com"
API_HOST = "https://api.youdo.com"

FEATURESETID_SIGNIN = "966"
FEATURESETID_DEVICE = "975"


def _new_device_identity() -> dict:
    device_id = os.urandom(8).hex()
    adv_id = str(uuid.uuid4())
    install_ts = int(time.time() * 1000)
    # Формат: androidSdk,appVer,platform,resolution,density,manufacturer,model,deviceId,installTs
    user_agent = f"28,1023,androidPhoneApp,1600x900,1.5,Redmi,23113RKC6C,{device_id},{install_ts}"
    return {
        "device_id": device_id,
        "adv_id": adv_id,
        "user_agent": user_agent
    }


class YoudoSession:
    def __init__(self):
        self.session = requests.Session()
        self.identity = _new_device_identity()
        self.msid = None
        self.user_id = None

    def request_sms_code(self, phone_e164: str, captcha_token: str) -> dict:
        """
            phone_e164 format: '+7 XXX XXX XX XX '
            captcha_token service: YandexSmarkCaptcha
        """
        url = f"{ROOT_HOST}/api/signin/generatecode/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "X-Featuresetid": FEATURESETID_SIGNIN,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.identity["user_agent"],
        }
        body = {
            "phoneE164": phone_e164,
            "deliveryMethod": 0,
            "captchaToken": captcha_token,
            "mode": "mobileapp",
        }
        
        response = self.session.post(url, headers=headers, json=body, timeout=15)
        response_json = response.json()

        return response_json

    def confirm_sms_code(self, phone_e164_dashed: str, code: str) -> dict:
        """
            phone_e164_dashed format: '+7 XXX XXX-XX-XX'
        """
        url = f"{ROOT_HOST}/api/signin/validatecode/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "X-Featuresetid": FEATURESETID_SIGNIN,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.identity["user_agent"],
        }
        body = {
            "code": code,
            "phoneE164": phone_e164_dashed,
            "mode": "mobileapp"
        }
        
        response = self.session.post(url, headers=headers, json=body, timeout=15)
        response_json = response.json()

        result = response_json.get("ResultObject", {})
        self.msid = result.get("msid")
        self.user_id = result.get("userID")

        return response_json

    def register_device_token(self, fcm_token: str) -> dict:
        if not self.msid:
            raise RuntimeError("Сначала выполните confirm_sms_code()")

        url = f"{API_HOST}/v110/device/adddevicetoken"
        body = {
            "deviceToken": fcm_token,
            "tokenServerType": 1,
            "DeviceUuid": self.identity["adv_id"],
        }

        sig_headers = generate_signature_headers(url, body)
        headers = {
            "Msid": self.msid,
            "User-Agent": self.identity["user_agent"],
            "X-Deviceid": self.identity["device_id"],
            "X-Advid": self.identity["adv_id"],
            "X-Visitorid": "",
            "X-Featuresetid": FEATURESETID_DEVICE,
            "Content-Type": "application/json; charset=UTF-8",
            **sig_headers,
        }
        import json
        body_str = json.dumps(body, separators=(",", ":"))

        response = self.session.post(url, headers=headers, data=body_str, timeout=15)
        response_json = response.json()

        return response_json


def main(captcha_token: str | None = None, fcm_token: str | None = None):
    yc = YoudoSession()

    phone = input("Phone (+7XXXXXXXXXX): ")
    phone_e164 = f"{phone[:2]} {phone[2:5]} {phone[5:8]} {phone[8:10]} {phone[10:]} "
    phone_e164_dashed = f"{phone[:2]} {phone[2:5]} {phone[5:8]}-{phone[8:10]}-{phone[10:]}"

    print(f"input: '{phone}'; e164: '{phone_e164}'; e164_dashed: '{phone_e164_dashed}';")
    correct = input("It's correct (Y/n)? ")
    if correct.lower() != "y":
        exit()

    if captcha_token is None:
        captcha_token = input("Captcha token: ")
    result = yc.request_sms_code(phone_e164, captcha_token)
    print(result)

    code = input("Code: ")
    result = yc.confirm_sms_code(phone_e164_dashed, code)
    print(result)

    if fcm_token is None:
        fcm_token = input("FCM token: ")
    result = yc.register_device_token(fcm_token)
    print(result)


if __name__ == "__main__":
    main()
