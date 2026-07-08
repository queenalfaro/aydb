
from pathlib import Path
from typing import Self

from .api import API
from .captcha import Captcha
from .config_manager import ConfigManager
from .fcm import FCM


class Client(API, FCM, Captcha, ConfigManager):

    WORKDIR = "."
    CONFIG_FILENAME = ".config.json"

    def __init__(
        self,
        phone: str | None = None,
        proxy: str | None = None,
        two_captcha_api_key: str | None = None,
        config_filename: str = CONFIG_FILENAME,
        workdir: str = WORKDIR,
    ) -> None:

        self.workdir = Path(workdir)
        self.config_filename = config_filename

        super().__init__()

        if not self.has_config:

            if phone:
                self.phone = phone
            else:
                correct = "n"
                while correct.lower() != "y":
                    self.phone = input("Phone (+7XXXXXXXXXX): ")
                    print(f"input: '{self.phone}';")
                    correct = input("It's correct (Y/n)? ")

            self.phone_e164 = f"{self.phone[:2]} {self.phone[2:5]} {self.phone[5:8]} {self.phone[8:10]} {self.phone[10:]} "
            self.phone_e164_dashed = f"{self.phone[:2]} {self.phone[2:5]} {self.phone[5:8]}-{self.phone[8:10]}-{self.phone[10:]}"

            self.proxy = proxy or input("Proxy: ") or None
            self.two_captcha_api_key = two_captcha_api_key or input("2Captcha api key: ")

    @classmethod
    async def create(cls, *args, **kwargs) -> Self:
        instance = cls(*args, **kwargs)
        if not instance.has_config:
            await instance.register()
            instance._set_config()
            instance.has_config = True
        return instance

    async def register(self) -> None:

        await self.checkin_or_register()
        captcha_token = self.solve_captcha()
        self.request_sms_code(self.phone_e164, captcha_token)

        correct = "n"
        while correct.lower() != "y":
            code = input("Code: ")
            print(f"input: '{code}';")
            correct = input("It's correct (Y/n)? ")

        self.confirm_sms_code(self.phone_e164_dashed, code)
        self.register_device_token(self.fcm_token)
