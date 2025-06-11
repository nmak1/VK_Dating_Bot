import requests
from typing import Optional, Dict, Any
from ..exceptions import APILimitError, InvalidRequestError
from ..exceptions import VKAPIError


class VKAPIClient:
    BASE_URL = "https://api.vk.com/method/"

    def __init__(self, access_token: str, api_version: str = "5.131"):
        self.access_token = access_token
        self.api_version = api_version

    def call_method(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        params.update({
            'access_token': self.access_token,
            'v': self.api_version
        })

        try:
            response = requests.post(
                f"{self.BASE_URL}{method}",
                params=params,
                timeout=10
            )
            data = response.json()

            if 'error' in data:
                error = data['error']
                if error.get('error_code') == 6:  # Too many requests
                    raise APILimitError(retry_after=1)
                raise InvalidRequestError(error.get('error_msg'), error.get('error_code'))

            return data.get('response', {})

        except requests.exceptions.RequestException as e:
            raise VKAPIError(f"Request failed: {str(e)}")