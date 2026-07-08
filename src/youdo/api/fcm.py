
class FCM:
    def register_device_token(self, fcm_token: str) -> dict:
        url = f"https://{self.API_HOST}/v110/device/adddevicetoken"
        body = {
            "deviceToken": fcm_token,
            "tokenServerType": 1,
            "DeviceUuid": self.adv_id,
        }
        headers = {
            "Msid": self.msid,
            "User-Agent": self.user_agent,
            "X-Deviceid": self.device_id,
            "X-Advid": self.adv_id,
            "X-Visitorid": "",
            "X-Featuresetid": self.AUTH_FEATURESETID,
            "Content-Type": "application/json; charset=UTF-8",
            **self.gen_signature_headers(url, body),
        }

        import json
        body_str = json.dumps(body, separators=(",", ":"))
        response = self.http_session.post(url, headers=headers, data=body_str, timeout=15)
        # response = self.http_session.post(url, headers=headers, json=body, timeout=15)
        print(response.status_code, len(response.text), response.text[:128])
        response_json = response.json()

        return response_json
