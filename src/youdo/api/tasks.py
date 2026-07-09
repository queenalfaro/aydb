
from urllib.parse import urlencode
import uuid


class Tasks:

    def get_tasks(
        self,
        page: int = 1,
        page_size: int = 50,
        q: str | None = None,
        category: str | None = None,
        status: str = 'Opened',
        **kwarks
    ):

        params = {
            'Page': str(page),
            'PageSize': str(page_size),
            'q': q or '',
            'onlySbr': 'false',
            'onlyB2B': 'false',
            'onlyVirtual': 'false',
            'onlyVacancies': 'false',
            'onlyShifts': 'false',
            'noOffers': 'false',
            'Category': category or '',
            'Status': status,
            'lat': '59.939095',
            'lng': '30.315868',
            'radius': '50.0',
            'searchRequestId': str(uuid.uuid4()),
            **kwarks
        }
        url = f'https://{self.API_HOST}/v110/tasks/tasks'
        headers = {
            'Host': self.API_HOST,
            'Msid': self.msid,
            'User-Agent': self.user_agent,
            'X-Deviceid': self.device_id,
            'X-Advid': self.adv_id,
            # 'X-Visitorid': '9985833256922135461',
            'X-Featuresetid': self.AUTH_FEATURESETID,
            **self.gen_signature_headers(f"{url}?{urlencode(params)}")
        }

        response = self.http_session.get(
            url, params=params, headers=headers, timeout=15)
        print(response.status_code, response.text)
        response_json = response.json()

        return response_json

    def get_task(self, id: str):
        params = {
            'id': id,
        }
        url = f'https://{self.API_HOST}/v110/tasks/task'
        headers = {
            'Host': self.API_HOST,
            'Msid': self.msid,
            'User-Agent': self.user_agent,
            'X-Deviceid': self.device_id,
            'X-Advid': self.adv_id,
            # 'X-Visitorid': '9985833256922135461',
            'X-Featuresetid': self.AUTH_FEATURESETID,
            **self.gen_signature_headers(f"{url}?{urlencode(params)}")
        }

        response = self.http_session.get(
            url, params=params, headers=headers, timeout=15)
        response_json = response.json()

        return response_json
