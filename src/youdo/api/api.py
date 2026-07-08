
import os
import time
import uuid

import requests

from .auth import Auth
from .fcm import FCM
from .get_config import GetConfig
from .signature import Signature
from .tasks import Tasks

class API(Auth, FCM, GetConfig, Signature, Tasks):

    ROOT_HOST = "youdo.com"
    API_HOST = "api.youdo.com"

    SIGNIN_FEATURESETID = "966"
    AUTH_FEATURESETID = "975"

    def __init__(self) -> None:
        super().__init__()

        if not self.has_config:
            self.device_id = os.urandom(8).hex()
            self.adv_id = str(uuid.uuid4())
            self.install_ts = int(time.time() * 1000)
            self.user_agent = f"28,1023,androidPhoneApp,1600x900,1.5,Redmi,23113RKC6C,{self.device_id},{self.install_ts}"
            self.msid = None
            self.user_id = None

        self.http_session = requests.Session()
