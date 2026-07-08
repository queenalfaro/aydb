"""
Патч push_receiver для приёма нативных (нешифрованных) Android push-сообщений.

Стоит посмотреть в сторону переноса на https://github.com/sdb9696/firebase-messaging.
"""
import asyncio
import json
import logging

import push_receiver.push_receiver as pr
import push_receiver.push_receiver
from push_receiver import listen

logging.basicConfig(level=logging.INFO)


def custom_listen(s, credentials, callback, persistent_ids, obj):
    pr.gcm_check_in(**credentials["gcm"])

    req = pr.LoginRequest()
    req.adaptive_heartbeat = False
    req.auth_service = 2
    req.auth_token = credentials["gcm"]["securityToken"]
    req.id = "chrome-63.0.3234.0"
    req.domain = "mcs.android.com"
    req.device_id = "android-%x" % int(credentials["gcm"]["androidId"])
    req.network_type = 1
    req.resource = credentials["gcm"]["androidId"]
    req.user = credentials["gcm"]["androidId"]
    req.use_rmq2 = True
    req.setting.add(name="new_vc", value="1")
    req.received_persistent_id.extend(persistent_ids)

    pr.__send(s, req)
    pr.__recv(s, first=True)
    logging.info("[*] Успешная авторизация в сокете Google MCS!")

    while True:
        p = pr.__recv(s)

        if p.__class__.__name__ == "HeartbeatPing":
            try:
                ack = pr.HeartbeatAck()
                ack.last_stream_id_received = p.last_stream_id_received
                pr.__send(s, ack)
                logging.info("[*] Отправлен HeartbeatAck (Pong)")
            except Exception as e:
                logging.warning(f"[-] Не удалось ответить на пинг: {e}")
            continue

        if type(p) is not pr.DataMessageStanza:
            continue

        has_crypto = any(x.key == "crypto-key" for x in p.app_data)
        if not has_crypto:
            callback(obj, None, p)
        else:
            # Сюда прилетит WebPush-пуш (маловероятно для нативного мобильного приложения)

            try:
                import http_ece
                import cryptography.hazmat.primitives.serialization as serialization
                from cryptography.hazmat.backends import default_backend
                from base64 import urlsafe_b64decode
                load_der_private_key = serialization.load_der_private_key
                
                crypto_key = pr.__app_data_by_key(p, "crypto-key")[3:]
                salt = pr.__app_data_by_key(p, "encryption")[5:]
                crypto_key = urlsafe_b64decode(crypto_key.encode("ascii"))
                salt = urlsafe_b64decode(salt.encode("ascii"))
                
                der_data = credentials["keys"]["private"]
                der_data = urlsafe_b64decode(der_data.encode("ascii") + b"========")
                secret = credentials["keys"]["auth"]
                secret = urlsafe_b64decode(secret.encode("ascii") + b"========")
                
                private_key = load_der_private_key(der_data, password=None, backend=default_backend())
                # Передаем как декодированное сообщение
                callback(obj, None, p)
            except Exception as e:
                logging.error(f"[-] Ошибка обработки зашифрованного пуша: {e}", exc_info=True)

            logging.warning("[-] Получен зашифрованный WebPush-пакет, пропущен")


def patch():
    pr.__listen = custom_listen


def on_notification(obj, notification, data_message):
    print("\n" + "=" * 60)
    print("[!] ПОЛУЧЕНО PUSH-УВЕДОМЛЕНИЕ!")
    print(f"Persistent ID сообщения: {data_message.persistent_id}")
    print("Данные сообщения (app_data):")
    for app_data in data_message.app_data:
        print(f"  {app_data.key}: {app_data.value}")
    print("=" * 60 + "\n")


def credentials_updated_callback(creds):
    print("CREDS UPDATED:", creds)


with open(".config.json") as f:
    config = json.load(f)

SECURITY_TOKEN = config["fcm"]["gcm"]["security_token"]
ANDROID_ID = config["fcm"]["gcm"]["android_id"]
print(ANDROID_ID, SECURITY_TOKEN)

# ANDROID_ID = "4218048154859198647"      # Взято из первой части AidLogin
# SECURITY_TOKEN = "4345064671142057014"  # Взято из CheckinTask_securityToken

credentials = {
    "gcm": {
        "androidId": ANDROID_ID,
        "securityToken": SECURITY_TOKEN,
    },
}

if __name__ == "__main__":
    print(f"[*] Инициализация подключения к mtalk.google.com...")
    print(f"[*] Используем Android ID: {ANDROID_ID}")
    try:
        push_receiver.push_receiver.__listen = custom_listen
        listen(credentials, on_notification, [])
    except KeyboardInterrupt:
        print("\n[*] Соединение закрыто пользователем.")
