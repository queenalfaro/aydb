import urllib.error
import urllib.parse
import urllib.request

from fid_installations import (
    APP_ID,
    CERT_SHA1,
    FIREBASE_APP_NAME_HASH,
    PACKAGE_NAME,
    PROJECT_NUMBER,
    register_installation,
)

CHECKIN_URL = "https://android.clients.google.com/checkin"
REGISTER3_URL = "https://android.clients.google.com/c2dm/register3"

APP_VER = "1023"
APP_VER_NAME = "4.0.261"
OSV = "28"
CLIV = "fcm-25.0.1"
GMSV = "220920023"
TARGET_VER = "36"

# --- protobuf-энамы из android_checkin.proto ---
DEVICE_CHROME_BROWSER = 3  # DeviceType.DEVICE_CHROME_BROWSER
PLATFORM_LINUX = 3  # ChromeBuildProto.Platform.PLATFORM_LINUX
CHANNEL_STABLE = 1  # ChromeBuildProto.Channel.CHANNEL_STABLE
CHECKIN_VERSION = 3
CHROME_VERSION = "63.0.3234.0"


# ---------------------------------------------------------------------------
# Голый protobuf wire-format (только то, что нужно: varint / fixed64 /
# length-delimited). Ничего похожего на google.protobuf не используется.
# ---------------------------------------------------------------------------

def _encode_varint(value: int) -> bytes:
    out = bytearray()
    v = value & 0xFFFFFFFFFFFFFFFF
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7


def _tag(field_no: int, wire_type: int) -> bytes:
    return _encode_varint((field_no << 3) | wire_type)


def _field_varint(field_no: int, value: int) -> bytes:
    return _tag(field_no, 0) + _encode_varint(value)


def _field_fixed64(field_no: int, value: int) -> bytes:
    return _tag(field_no, 1) + (value & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "little")


def _field_bytes(field_no: int, value: bytes) -> bytes:
    return _tag(field_no, 2) + _encode_varint(len(value)) + value


def _field_string(field_no: int, value: str) -> bytes:
    return _field_bytes(field_no, value.encode("utf-8"))


def _field_message(field_no: int, message: bytes) -> bytes:
    return _field_bytes(field_no, message)


def _parse_message(buf: bytes) -> dict[int, list]:
    """
    Минимальный разбор protobuf-сообщения: field_no -> [значения].
    varint и fixed64 остаются int, length-delimited остаётся bytes.
    """
    fields: dict[int, list] = {}
    pos, n = 0, len(buf)
    while pos < n:
        key, pos = _read_varint(buf, pos)
        field_no, wire_type = key >> 3, key & 0x7
        if wire_type == 0:  # varint
            value, pos = _read_varint(buf, pos)
        elif wire_type == 1:  # fixed64
            value = int.from_bytes(buf[pos:pos + 8], "little")
            pos += 8
        elif wire_type == 2:  # length-delimited
            length, pos = _read_varint(buf, pos)
            value = buf[pos:pos + length]
            pos += length
        elif wire_type == 5:  # fixed32
            value = int.from_bytes(buf[pos:pos + 4], "little")
            pos += 4
        else:
            raise ValueError(f"неизвестный wire type {wire_type} в ответе checkin")
        fields.setdefault(field_no, []).append(value)
    return fields


# ---------------------------------------------------------------------------
# GCM checkin
# ---------------------------------------------------------------------------

def _build_checkin_request(android_id: int, security_token: int) -> bytes:
    chrome_build = (
        _field_varint(1, PLATFORM_LINUX)
        + _field_string(2, CHROME_VERSION)
        + _field_varint(3, CHANNEL_STABLE)
    )
    checkin_proto = (
        _field_varint(12, DEVICE_CHROME_BROWSER)
        + _field_message(13, chrome_build)
    )

    body = b""
    if android_id:
        body += _field_varint(2, android_id)
    body += _field_message(4, checkin_proto)
    if security_token:
        body += _field_fixed64(13, security_token)
    body += _field_varint(14, CHECKIN_VERSION)
    body += _field_varint(22, 0)  # user_serial_number
    return body


def gcm_check_in(android_id=None, security_token=None, **kwargs) -> dict:
    """
    Выполняет GCM checkin (замена push_receiver.gcm_check_in).

    android_id / security_token можно передать, если checkin уже выполнялся
    раньше; без них Google выдаёт новую пару, как для первого включения
    нового телефона.
    """
    payload = _build_checkin_request(
        int(android_id) if android_id else 0,
        int(security_token) if security_token else 0,
    )

    req = urllib.request.Request(
        CHECKIN_URL,
        data=payload,
        headers={"Content-Type": "application/x-protobuf"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_data = resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"checkin вернул HTTP {e.code}: {e.read().decode('utf-8', 'replace')}"
        ) from e

    fields = _parse_message(resp_data)
    if 7 not in fields or 8 not in fields:
        raise RuntimeError(f"в ответе checkin нет androidId/securityToken: {fields}")

    return {
        "androidId": fields[7][0],
        "securityToken": fields[8][0],
    }


# ---------------------------------------------------------------------------
# register3 + Firebase Installation
# ---------------------------------------------------------------------------

def do_full_registration(androidId=None, securityToken=None, **kwargs) -> dict:
    # GCM checkin БЕЗ androidId/securityToken -> Google выдаёт новую пару,
    # как для первого включения нового телефона.
    checkin = gcm_check_in(androidId, securityToken, **kwargs)
    android_id = checkin["androidId"]
    security_token = checkin["securityToken"]

    installation = register_installation()

    body = {
        "X-subtype": PROJECT_NUMBER,
        "sender": PROJECT_NUMBER,
        "X-app_ver": APP_VER,
        "X-osv": OSV,
        "X-cliv": CLIV,
        "X-gmsv": GMSV,
        "X-appid": installation["fid"],
        "X-scope": "*",
        "X-Goog-Firebase-Installations-Auth": installation["auth_token"],
        "X-gmp_app_id": APP_ID,
        "X-firebase-app-name-hash": FIREBASE_APP_NAME_HASH,
        "X-app_ver_name": APP_VER_NAME,
        "app": PACKAGE_NAME,
        "device": android_id,
        "app_ver": APP_VER,
        "gcm_ver": GMSV,
        "plat": "0",
        "cert": CERT_SHA1.lower(),
        "target_ver": TARGET_VER,
        # "info": ...
    }
    headers = {
        "Authorization": f"AidLogin {android_id}:{security_token}",
        "App": PACKAGE_NAME,
        "Gcm_ver": GMSV,
        "User-Agent": "Android-GCM/1.5",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = urllib.parse.urlencode(body).encode("utf-8")
    req = urllib.request.Request(REGISTER3_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            response_text = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"register3 вернул HTTP {e.code}: {e.read().decode('utf-8', 'replace')}"
        ) from e

    if "Error" in response_text:
        raise RuntimeError(f"register3 вернул ошибку: {response_text}")

    fcm_token = response_text.split("=", 1)[1].strip()

    return {
        "gcm": {
            "androidId": android_id,
            "securityToken": security_token,
            "secret": "AAAAAAAAAAAAAAAAAAAAAA==",
            "privateKey": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        },
        "fcm": {"token": fcm_token},
        "installation": installation,
    }


if __name__ == "__main__":
    import json

    creds = do_full_registration()
    print(json.dumps(creds, indent=2, ensure_ascii=False))
