"""
Firebase Installations API.

Генерирует новый Firebase Installation ID (FID) "с нуля" (как для нового
устройства) и регистрирует его в проекте YouDo, получая installations auth
token — он понадобится на шаге регистрации (register3), чтобы привязать
push-токен именно к этому FID.
"""
import base64
import json
import os
import time

import requests

PROJECT_ID = "firebase-appios"
PROJECT_NUMBER = "830888382366"
APP_ID = "1:830888382366:android:538f60488644afda"
API_KEY = "AIzaSyD6EI_g--9tS4kvFVhndIOe_pWg__ujkEQ"
PACKAGE_NAME = "com.sebbia.youdo"
CERT_SHA1 = "88979E9A847FE16AB3587F089C2432A7C292AE08"
FIREBASE_APP_NAME_HASH = "R1dAH9Ui7M-ynoznwBdw01tLxhI"

INSTALLATIONS_URL = f"https://firebaseinstallations.googleapis.com/v1/projects/{PROJECT_ID}/installations"


def generate_fid() -> str:
    """
    Генерирует новый случайный Firebase Installation ID (FID).

    Алгоритм соответствует официальному Firebase SDK (проверено по исходникам
    python-порта firebase-messaging).
    """
    fid_bytes = bytearray(os.urandom(17))
    fid_bytes[0] = 0b01110000 + (fid_bytes[0] % 0b00010000)
    encoded = base64.urlsafe_b64encode(bytes(fid_bytes)).decode("ascii")
    return encoded[:22]


def register_installation(sdk_version: str = "a:17.0.0") -> dict:
    """
    Регистрирует новый FID в Firebase Installations API.

    Тело оригинального запроса закодировано/зашифровано. Использую просто 
    JSON, так как работает. Значение "sdkVersion" (обычно формат "a:XX.Y.Z" 
    для Android) здесь — правдоподобная догадка, а не подтвержденный факт.
    """
    fid = generate_fid()
    payload = {
        "fid": fid,
        "appId": APP_ID,
        "authVersion": "FIS_v2",
        "sdkVersion": sdk_version,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Android-Package": PACKAGE_NAME,
        "X-Android-Cert": CERT_SHA1,
        "x-goog-api-key": API_KEY,
    }

    response = requests.post(
        INSTALLATIONS_URL, headers=headers, data=json.dumps(payload), timeout=15
    )
    response.raise_for_status()
    response_json = response.json()

    return {
        "fid": response_json["fid"],
        "auth_token": response_json["authToken"]["token"],
        "refresh_token": response_json["refreshToken"],
        "expires_in": response_json["authToken"]["expiresIn"],
        "created_at": time.time(),
    }


if __name__ == "__main__":
    result = register_installation()
    print(result)
