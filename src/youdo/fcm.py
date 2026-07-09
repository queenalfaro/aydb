
import asyncio
import logging
from typing import Any

from firebase_messaging.android_fcmregister import AndroidRegisterConfig
from firebase_messaging.android_fcmpushclient import AndroidPushClient


_logger = logging.getLogger(__name__)


class FCM():

    PROJECT_ID = "firebase-appios"
    APP_ID = "1:830888382366:android:538f60488644afda"
    API_KEY = "AIzaSyD6EI_g--9tS4kvFVhndIOe_pWg__ujkEQ"
    MESSAGING_SENDER_ID = "830888382366"
    BUNDLE_ID = "com.sebbia.youdo"
    CHROME_VERSION = "94.0.4606.51"
    CERT_SHA1 = "88979E9A847FE16AB3587F089C2432A7C292AE08"
    FIREBASE_APP_NAME_HASH = "R1dAH9Ui7M-ynoznwBdw01tLxhI"
    APP_VERSION = "1023",
    APP_VERSION_NAME = "4.0.261",

    def __init__(self) -> None:
        super().__init__()

        fcm_config = AndroidRegisterConfig(
            project_id=self.PROJECT_ID,
            app_id=self.APP_ID,
            api_key=self.API_KEY,
            messaging_sender_id=self.MESSAGING_SENDER_ID,
            bundle_id=self.BUNDLE_ID,
            cert_sha1=self.CERT_SHA1,
            app_name_hash=self.FIREBASE_APP_NAME_HASH,
            app_ver=self.APP_VERSION,
            app_ver_name=self.APP_VERSION_NAME,
        )

        self.fcm_client = AndroidPushClient(
            callback=self.on_fmc_notification,
            fcm_config=fcm_config,
            credentials=self.fcm_credentials,
            credentials_updated_callback=self.fmc_credentials_updated_callback,
        )

    @property
    def fcm_token(self) -> str:
        return self.fcm_client.credentials["fcm"]["registration"]["token"]

    def on_fmc_notification(self, data: dict, persistent_id: str, context: Any) -> None:
        print("\n" + "="*60)
        print("[!] ПОЛУЧЕНО PUSH-УВЕДОМЛЕНИЕ!")
        print(f"Persistent ID сообщения: {persistent_id}")
        print("Данные сообщения (app_data):")
        for k, v in data.items():
            if k == "_raw_msg":
                continue
            print(f"  {k}: {v}")
        print("="*60 + "\n")

    def fmc_credentials_updated_callback(self, creds):
        self._set_creds()

    async def checkin_or_register(self) -> None:
        await self.fcm_client.checkin_or_register()

    async def start_listener(self):
        print(f"\nЗапустил приемник уведомлений...\n")

        try:
            await self.fcm_client.start()

            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n[*] Завершение работы клиента...")
        finally:
            await self.fcm_client.stop()
