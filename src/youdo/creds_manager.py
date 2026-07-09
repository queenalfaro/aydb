
import json
import os
from typing import Any


class CredsManager:

    def __init__(self):
        super().__init__()

        self.creds = {}
        self._get_creds()
        self.has_creds = bool(self.creds)

        self.phone = self.creds.get("base", {}).get("phone")
        self.proxy = self.creds.get("base", {}).get("proxy")
        self.two_captcha_api_key = self.creds.get(
            "base", {}).get("two_captcha_api_key")

        self.device_id = self.creds.get("api", {}).get("device_id")
        self.adv_id = self.creds.get("api", {}).get("adv_id")
        self.install_ts = self.creds.get("api", {}).get("install_ts")
        self.user_agent = self.creds.get("api", {}).get("user_agent")
        self.msid = self.creds.get("api", {}).get("msid")
        self.user_id = self.creds.get("api", {}).get("user_id")

        self.fcm_credentials = self.creds.get("fcm")

    def _get_creds(self) -> dict[str, Any]:
        self.creds = {}
        if os.path.exists(self.workdir / self.creds_filename):
            with open(self.workdir / self.creds_filename, "r", encoding="utf-8") as f:
                self.creds = json.load(f)
        return self.creds

    def _set_creds(self) -> None:
        self.creds = {
            "base": {
                "phone": self.phone,
                "proxy": self.proxy,
                "two_captcha_api_key": self.two_captcha_api_key,
            },
            "api": {
                "device_id": self.device_id,
                "adv_id": self.adv_id,
                "install_ts": self.install_ts,
                "user_agent": self.user_agent,
                "msid": self.msid,
                "user_id": self.user_id,
            },
            "fcm": self.fcm_client.credentials,
        }
        with open(self.workdir / self.creds_filename, "w", encoding="utf-8") as f:
            json.dump(self.creds, f, indent=4)
