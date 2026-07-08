
import json
import os
from typing import Any


class ConfigManager:

    def __init__(self):
        super().__init__()

        self.config = {}
        self._get_config()
        self.has_config = bool(self.config)

        self.phone = self.config.get("base", {}).get("phone")
        self.proxy = self.config.get("base", {}).get("proxy")
        self.two_captcha_api_key = self.config.get("base", {}).get("two_captcha_api_key")

        self.device_id = self.config.get("api", {}).get("device_id")
        self.adv_id = self.config.get("api", {}).get("adv_id")
        self.install_ts = self.config.get("api", {}).get("install_ts")
        self.user_agent = self.config.get("api", {}).get("user_agent")
        self.msid = self.config.get("api", {}).get("msid")
        self.user_id = self.config.get("api", {}).get("user_id")

        self.fcm_credentials = self.config.get("fcm")

    def _get_config(self) -> dict[str, Any]:
        self.config = {}
        if os.path.exists(self.workdir / self.config_filename):
            with open(self.workdir / self.config_filename, "r", encoding="utf-8") as f:
                self.config = json.load(f)

    def _set_config(self) -> None:
        self.config = {
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
        with open(self.workdir / self.config_filename, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)
