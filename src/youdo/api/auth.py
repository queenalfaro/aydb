
class Auth:

    def request_sms_code(self, phone_e164: str, captcha_token: str) -> dict:
        """
            phone_e164 format: '+7 XXX XXX XX XX '
            captcha_token service: YandexSmarkCaptcha
        """
        url = f"https://{self.ROOT_HOST}/api/signin/generatecode/"
        body = {
            "phoneE164": phone_e164,
            "deliveryMethod": 0,
            "captchaToken": captcha_token,
            "mode": "mobileapp",
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "X-Featuresetid": self.SIGNIN_FEATURESETID,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.user_agent,
            **self.gen_signature_headers(url, body)
        }

        response = self.http_session.post(url, headers=headers, json=body, timeout=15)
        print(response.status_code, len(response.text), response.text[:128])
        response_json = response.json()

        return response_json

    def confirm_sms_code(self, phone_e164_dashed: str, code: str) -> dict:
        """
            phone_e164_dashed format: '+7 XXX XXX-XX-XX'
            code: sms-code or last 4 digits of the calling phone number
        """
        url = f"https://{self.ROOT_HOST}/api/signin/validatecode/"
        body = {
            "code": code,
            "phoneE164": phone_e164_dashed,
            "mode": "mobileapp"
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "X-Featuresetid": self.SIGNIN_FEATURESETID,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.user_agent,
            **self.gen_signature_headers(url, body)
        }

        response = self.http_session.post(url, headers=headers, json=body, timeout=15)
        print(response.status_code, len(response.text), response.text[:128])
        response_json = response.json()

        result = response_json.get("ResultObject", {})
        self.msid = result.get("msid")
        self.user_id = result.get("userID")

        return response_json
