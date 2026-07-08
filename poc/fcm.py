import asyncio
import time
from typing import Any
import json

from firebase_messaging.fcmregister import FcmRegister, FcmRegisterConfig
from firebase_messaging.fcmpushclient import FcmPushClient


PROJECT_ID = "firebase-appios"
APP_ID = "1:830888382366:android:538f60488644afda"
API_KEY = "AIzaSyD6EI_g--9tS4kvFVhndIOe_pWg__ujkEQ"
MESSAGING_SENDER_ID = "830888382366"
BUNDLE_ID = "com.sebbia.youdo"
CHROME_VERSION = "94.0.4606.51"

with open(".config.json") as f:
    config = json.load(f)
CREDS = config["fcm"]

def on_notification(data: dict, persistent_id: str, context: Any) -> None:
    print("\n" + "="*60)
    print("[!] ПОЛУЧЕНО PUSH-УВЕДОМЛЕНИЕ!")
    print(f"Persistent ID сообщения: {persistent_id}")
    print("Данные сообщения (app_data):")
    for k, v in data.items():
        print(k, v)
        if k == "_raw_msg":
            continue
        print(f"  {k}: {v}")
    print("="*60 + "\n")

def credentials_updated_callback(creds):
    print("NEW CREDS:", creds)


async def create_client():
    fcm_config = FcmRegisterConfig(
        project_id=PROJECT_ID,
        app_id=APP_ID,
        api_key=API_KEY,
        messaging_sender_id=MESSAGING_SENDER_ID,
        bundle_id=BUNDLE_ID,
        chrome_version=CHROME_VERSION
    )

    client = FcmPushClient(
        callback=on_notification,
        fcm_config=fcm_config,
        credentials=CREDS,
        credentials_updated_callback=credentials_updated_callback,
    )

    fcm_token = await client.checkin_or_register()
    print(f"\n[Успешно] Получен FCM Token: {fcm_token}\n")

    return client


async def start_listener(client):
    print(f"\nЗапустил приемник уведомлений...\n")

    try:
        await client.start()

        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n[*] Завершение работы клиента...")
    finally:
        await client.stop()


async def main():
    client = await create_client()
    await start_listener(client)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
