import logging
import asyncio
import secrets
import time
from base64 import b64encode
from typing import Any

from aiohttp import ClientSession
from firebase_messaging.fcmpushclient import FcmPushClient, ErrorType
from firebase_messaging.fcmregister import FcmRegister, FcmRegisterConfig
from firebase_messaging.proto.mcs_pb2 import DataMessageStanza

_logger = logging.getLogger(__name__)

PACKAGE_NAME = "com.sebbia.youdo"
CERT_SHA1 = "88979E9A847FE16AB3587F089C2432A7C292AE08"
FIREBASE_APP_NAME_HASH = "R1dAH9Ui7M-ynoznwBdw01tLxhI"

# =====================================================================
# ВСТАВЬТЕ СЮДА ВАШИ РАБОЧИЕ ДАННЫЕ (которые уже привязаны к YouDo)
# =====================================================================
ANDROID_ID = "4218048154859198647"      
SECURITY_TOKEN = "4345064671142057014"  

credentials = {
    "gcm": {
        "android_id": ANDROID_ID,
        "security_token": SECURITY_TOKEN,
        "secret": "AAAAAAAAAAAAAAAAAAAAAA==",
        "privateKey": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    }
}
credentials = {'keys': {'public': 'BNDaGE_YSpA2pB6cRUMr54QjRD_bzCVI4mvRg9PLgDuNzOgojQHbVw9fQC7WXizPd5i7b2XfuFH5rmCXdtNQSjM=', 'private': 'MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgBDyTyOGqbIYD0ZvBwg95vnZ0BlR3NxzHfgo-r8PcgJqhRANCAATQ2hhP2EqQNqQenEVDK-eEI0Q_28wlSOJr0YPTy4A7jczoKI0B21cPX0Au1l4sz3eYu29l37hR-a5gl3bTUEoz', 'secret': '05xo4TrVVj0R5-t6s4QEHw=='}, 'gcm': {'android_id': '4891990962900961636', 'security_token': '2790880429824916551', 'app_id': 'com.sebbia.youdo'}, 'fcm': {'registration': {'token': 'dNDCO8YwY1nsoyeMlIZnGY:APA91bFafFPXvTMw6AGnUtNVGOKDeznq9fWTgA8YmfcdQN3QDmWCgvZyE7Aty9KTUJ4qDYRd5OtOJxw7j_Ajx0uCSm-8z1m3wB8ix78vb2EoSiNx3Swhco4'}}, 'installation': {'fid': 'dNDCO8YwY1nsoyeMlIZnGY', 'auth_token': 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBJZCI6IjE6ODMwODg4MzgyMzY2OmFuZHJvaWQ6NTM4ZjYwNDg4NjQ0YWZkYSIsImV4cCI6MTc4NDExNzMwNiwiZmlkIjoiZE5EQ084WXdZMW5zb3llTWxJWm5HWSIsInByb2plY3ROdW1iZXIiOjgzMDg4ODM4MjM2Nn0.AB2LPV8wRQIhAJ4VWo1dmQSWO7UvBNeW1g8uIC9HGpt-xMPHdSMJp10nAiBGeFoPB64QnuOMQ_4pZGHYKvmKN5lcFKkZu3zggbReig', 'refresh_token': '3_AS3qfwLygzHH-QZdSOoQ2-8ZH2P2ai3LeAa56pufjtnxrA-DNlDYQNQ6liAxqItf0ZCbIKPFNnmGR5qoyouVgU7uQc3qm6UnrbNqJBetmNu5j3A', 'expires_in': 604800, 'created_at': 1783512505.6248512}, 'config': {'bundle_id': 'com.sebbia.youdo', 'project_id': 'firebase-appios', 'vapid_key': 'BDOU99-h67HcA6JeFXHbSNMu7e2yNNu3RzoMj8TM4W88jITfq7ZmPvIM1Iv-4_l2LxQcYwhqby2xGpWwzjfAnG4'}}
# =====================================================================


class AndroidFcmRegister(FcmRegister):
    def __init__(
        self,
        config: FcmRegisterConfig,
        credentials: dict | None = None,
        credentials_updated_callback: Any | None = None,
        *,
        cert_sha1: str,
        app_name_hash: str,
        http_client_session: ClientSession | None = None,
        log_debug_verbose: bool = False,
    ):
        super().__init__(
            config=config,
            credentials=credentials,
            credentials_updated_callback=credentials_updated_callback,
            http_client_session=http_client_session,
            log_debug_verbose=log_debug_verbose,
        )
        self.cert_sha1 = cert_sha1
        self.app_name_hash = app_name_hash

    async def checkin_or_register(self) -> dict[str, Any]:
        # Если учетные данные переданы, проверяем и нормализуем их структуру
        if self.credentials and "gcm" in self.credentials:
            gcm_data = self.credentials["gcm"]
            # Поддерживаем как camelCase из старого скрипта, так и snake_case из нового
            aid = gcm_data.get("android_id") or gcm_data.get("androidId")
            tok = gcm_data.get("security_token") or gcm_data.get("securityToken")

            if aid and tok:
                try:
                    # Выполняем проверочный Check-in в Google
                    gcm_response = await self.gcm_check_in(int(aid), int(tok))
                    if gcm_response:
                        # Приводим структуру к строгому формату библиотеки fcmpushclient
                        self.credentials["gcm"]["android_id"] = str(aid)
                        self.credentials["gcm"]["security_token"] = str(tok)
                        self.credentials["gcm"].setdefault("app_id", self.config.bundle_id)
                        
                        # Предотвращаем KeyError для FCM-токена в fcmpushclient.py
                        fcm_struct = self.credentials.setdefault("fcm", {})
                        reg_struct = fcm_struct.setdefault("registration", {})
                        if "token" not in reg_struct:
                            # Пытаемся взять токен из старых полей или используем заглушку
                            old_token = self.credentials.get("fcm", {}).get("token") or "dummy_token"
                            reg_struct["token"] = old_token
                        
                        # Проверяем наличие ключей дешифрования
                        self.credentials.setdefault("keys", {
                            "private": self.credentials["gcm"].get("privateKey", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="),
                            "secret": self.credentials["gcm"].get("secret", "AAAAAAAAAAAAAAAAAAAAAA=="),
                            "public": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
                        })
                        
                        _logger.info("Существующие учетные данные успешно проверены и нормализованы.")
                        return self.credentials
                except Exception as e:
                    _logger.warning("Check-in с существующими creds не удался (%s). Перерегистрируемся...", e)

        # Если credentials отсутствуют или невалидны — регистрируем новое "устройство"
        self.credentials = await self.register_android()
        if self.credentials_updated_callback:
            self.credentials_updated_callback(self.credentials)

        return self.credentials

    async def register_android(self) -> dict[str, Any]:
        keys = self.generate_keys()

        checkin_data = await self.gcm_check_in()
        if not checkin_data:
            raise RuntimeError("GCM Check-in завершился ошибкой")

        android_id = str(checkin_data["androidId"])
        security_token = str(checkin_data["securityToken"])

        installation = await self._fcm_install_android()
        if not installation:
            raise RuntimeError("Firebase Installation завершилась ошибкой")

        fcm_token = await self._gcm_register_android(android_id, security_token, installation)
        if not fcm_token:
            raise RuntimeError("GCM register3 завершился ошибкой")

        res = {
            "keys": keys,
            "gcm": {
                "android_id": android_id,
                "security_token": security_token,
                "app_id": self.config.bundle_id,
            },
            "fcm": {
                "registration": {
                    "token": fcm_token
                }
            },
            "installation": installation,
            "config": {
                "bundle_id": self.config.bundle_id,
                "project_id": self.config.project_id,
                "vapid_key": self.config.vapid_key,
            },
        }
        return res

    async def _fcm_install_android(self) -> dict | None:
        fid = bytearray(secrets.token_bytes(17))
        fid[0] = 0b01110000 + (fid[0] % 0b00010000)
        fid64 = b64encode(fid).decode()[:22]

        headers = {
            "Content-Type": "application/json",
            "X-Android-Package": self.config.bundle_id,
            "X-Android-Cert": self.cert_sha1,
            "x-goog-api-key": self.config.api_key,
        }
        payload = {
            "fid": fid64,
            "appId": self.config.app_id,
            "authVersion": "FIS_v2",
            "sdkVersion": "a:17.0.0",
        }
        url = f"https://firebaseinstallations.googleapis.com/v1/projects/{self.config.project_id}/installations"

        async with self._session.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=self.CLIENT_TIMEOUT,
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "fid": data["fid"],
                    "auth_token": data["authToken"]["token"],
                    "refresh_token": data["refreshToken"],
                    "expires_in": int(data["authToken"]["expiresIn"][:-1]),
                    "created_at": time.time(),
                }
            else:
                text = await resp.text()
                _logger.error("Ошибка во время Android fcm_install: %s", text)
                return None

    async def _gcm_register_android(
        self, android_id: str, security_token: str, installation: dict
    ) -> str | None:
        body = {
            "X-subtype": self.config.messaging_sender_id,
            "sender": self.config.messaging_sender_id,
            "X-app_ver": "1023",
            "X-osv": "28",
            "X-cliv": "fcm-25.0.1",
            "X-gmsv": "220920023",
            "X-appid": installation["fid"],
            "X-scope": "*",
            "X-Goog-Firebase-Installations-Auth": installation["auth_token"],
            "X-gmp_app_id": self.config.app_id,
            "X-firebase-app-name-hash": self.app_name_hash,
            "X-app_ver_name": "4.0.261",
            "app": self.config.bundle_id,
            "device": android_id,
            "app_ver": "1023",
            "gcm_ver": "220920023",
            "plat": "0",
            "cert": self.cert_sha1.lower(),
            "target_ver": "36",
        }
        headers = {
            "Authorization": f"AidLogin {android_id}:{security_token}",
            "App": self.config.bundle_id,
            "Gcm_ver": "220920023",
            "User-Agent": "Android-GCM/1.5",
        }
        url = "https://android.clients.google.com/c2dm/register3"

        async with self._session.post(
            url=url,
            headers=headers,
            data=body,
            timeout=self.CLIENT_TIMEOUT,
        ) as resp:
            resp_text = await resp.text()
            if resp.status == 200 and "Error" not in resp_text:
                fcm_token = resp_text.split("=", 1)[1].strip()
                return fcm_token
            else:
                _logger.error("Ошибка во время Android register3: %s", resp_text)
                return None


class AndroidPushClient(FcmPushClient):
    def __init__(
        self,
        callback,
        fcm_config,
        credentials=None,
        credentials_updated_callback=None,
        *,
        cert_sha1: str,
        app_name_hash: str,
        callback_context=None,
        received_persistent_ids=None,
        config=None,
        http_client_session=None,
    ):
        super().__init__(
            callback,
            fcm_config,
            credentials,
            credentials_updated_callback,
            callback_context=callback_context,
            received_persistent_ids=received_persistent_ids,
            config=config,
            http_client_session=http_client_session,
        )
        self.cert_sha1 = cert_sha1
        self.app_name_hash = app_name_hash

    async def checkin_or_register(self) -> str:
        self.register = AndroidFcmRegister(
            self.fcm_config,
            self.credentials,
            self.credentials_updated_callback,
            cert_sha1=self.cert_sha1,
            app_name_hash=self.app_name_hash,
            http_client_session=self._http_client_session,
        )
        self.credentials = await self.register.checkin_or_register()
        await self.register.close()
        return self.credentials["fcm"]["registration"]["token"]

    def _handle_data_message(self, msg: DataMessageStanza) -> None:
        if (
            self._app_data_by_key(msg, "message_type", do_not_raise=True)
            == "deleted_messages"
        ):
            return

        has_crypto = any(x.key == "crypto-key" for x in msg.app_data)

        if not has_crypto:
            print("UNCRYPTED")
            app_data_dict = {x.key: x.value for x in msg.app_data}
            app_data_dict["_raw_msg"] = msg
            
            try:
                self.callback(app_data_dict, msg.persistent_id, self.callback_context)
                self._reset_error_count(ErrorType.NOTIFY)
            except Exception as e:
                self._try_increment_error_count(ErrorType.NOTIFY)
                logging.error(e, exc_info=True)
        else:
            print("CRYPTED")
            super()._handle_data_message(msg)


def on_notification(data: dict, persistent_id: str, context: Any) -> None:
    print("\n" + "="*60)
    print("[!] ПОЛУЧЕНО PUSH-УВЕДОМЛЕНИЕ!")
    print(f"Persistent ID сообщения: {persistent_id}")
    print("Данные сообщения (app_data):")
    for k, v in data.items():
        if k == "_raw_msg":
            continue
        print(f"  {k}: {v}")
    print("="*60 + "\n")


def credentials_updated_callback(creds):
    print("CREDS UPDATED:", creds)


async def main():
    logging.basicConfig(level=logging.INFO)

    fcm_config = FcmRegisterConfig(
        project_id="firebase-appios",
        app_id="1:830888382366:android:538f60488644afda",
        api_key="AIzaSyD6EI_g--9tS4kvFVhndIOe_pWg__ujkEQ",
        messaging_sender_id="830888382366",   
        bundle_id=PACKAGE_NAME,                
        chrome_version="94.0.4606.51"
    )

    client = AndroidPushClient(
        callback=on_notification,
        fcm_config=fcm_config,
        credentials=credentials,  # Используем существующие привязанные данные
        credentials_updated_callback=credentials_updated_callback,
        cert_sha1=CERT_SHA1,
        app_name_hash=FIREBASE_APP_NAME_HASH,
    )

    fcm_token = await client.checkin_or_register()
    print(f"\n[Информация] Используется FCM Token: {fcm_token}\n")

    try:
        await client.start()
        
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n[*] Завершение работы клиента...")
    finally:
        await client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass