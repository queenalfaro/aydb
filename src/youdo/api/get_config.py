
class GetConfig:

    def get_config(self) -> dict:

        url = f'https://{self.API_HOST}/v110/Service/GetConfig'
        headers = {
            'Host': self.API_HOST,
            'User-Agent': self.user_agent,
            'X-Deviceid': self.device_id,
            'X-Advid': self.adv_id,
            'X-Featuresetid': self.AUTH_FEATURESETID,
            **self.gen_signature_headers(url)
        }

        response = self.http_session.get(url, headers=headers, timeout=15)
        response_json = response.json()

        return response_json
