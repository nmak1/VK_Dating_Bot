import time

import requests
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

import logging
from pydantic import BaseModel, json

from core import VKAPIError
from core.exceptions import APILimitError, InvalidRequestError

logger = logging.getLogger(__name__)


class VKAPIClient:
    BASE_URL = "https://api.vk.com/method/"
    DEFAULT_TIMEOUT = 10

    def __init__(self, access_token: str, api_version: str = "5.131"):
        self.access_token = access_token
        self.api_version = api_version
        self.session = requests.Session()
        self.last_call_time = None

    def call_method(self,
                    method: str,
                    params: Optional[Dict[str, Any]] = None,
                    timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Базовый метод для вызова API VK

        Args:
            method: Название метода API (например, 'users.get')
            params: Параметры запроса
            timeout: Таймаут запроса в секундах

        Returns:
            Ответ от API в виде словаря

        Raises:
            APILimitError: При превышении лимитов запросов
            InvalidRequestError: При ошибках в запросе
            VKAPIError: При других ошибках API
        """
        params = params or {}
        params.update({
            'access_token': self.access_token,
            'v': self.api_version,
            'lang': 'ru'  # Для русскоязычных ответов
        })

        try:
            self._rate_limit_delay()

            response = self.session.post(
                f"{self.BASE_URL}{method}",
                params=params,
                timeout=timeout or self.DEFAULT_TIMEOUT
            )
            data = response.json()
            self.last_call_time = datetime.now()

            if 'error' in data:
                self._handle_api_error(data['error'])

            return data.get('response', {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Request to VK API failed: {str(e)}")
            raise VKAPIError(f"Request failed: {str(e)}")

    def _handle_api_error(self, error_data: Dict[str, Any]):
        """Обработка ошибок API"""
        error_code = error_data.get('error_code')
        error_msg = error_data.get('error_msg', 'Unknown error')

        if error_code == 6:  # Too many requests
            retry_after = error_data.get('request_params', {}).get('retry_after', 1)
            raise APILimitError(retry_after=retry_after)
        elif error_code in [5, 17]:  # Auth errors
            raise InvalidRequestError("Authentication failed", error_code)
        else:
            raise InvalidRequestError(error_msg, error_code)

    def _rate_limit_delay(self):
        """Задержка для соблюдения лимитов API"""
        if self.last_call_time:
            elapsed = (datetime.now() - self.last_call_time).total_seconds()
            if elapsed < 0.34:  # ~3 запроса в секунду
                time.sleep(0.34 - elapsed)

    # Специфичные методы API
    def get_user(self, user_id: Union[int, str], fields: str = '') -> Dict[str, Any]:
        """
        Получение информации о пользователе

        Args:
            user_id: ID пользователя или screen_name
            fields: Дополнительные поля (например, 'city,photo_max')

        Returns:
            Информация о пользователе
        """
        params = {
            'user_ids': user_id,
            'fields': fields or 'photo_max,domain,city,sex,bdate'
        }
        response = self.call_method('users.get', params)
        return response[0] if response else {}

    def send_message(self,
                     user_id: int,
                     message: str,
                     keyboard: Optional[Dict] = None,
                     attachment: Optional[str] = None) -> int:
        """
        Отправка сообщения пользователю

        Args:
            user_id: ID получателя
            message: Текст сообщения
            keyboard: Клавиатура в формате VK API
            attachment: Вложения (photo123_456)

        Returns:
            ID отправленного сообщения
        """
        params = {
            'user_id': user_id,
            'message': message,
            'random_id': int(datetime.now().timestamp())
        }

        if keyboard:
            params['keyboard'] = json.dumps(keyboard)
        if attachment:
            params['attachment'] = attachment

        return self.call_method('messages.send', params).get('message_id')

    def get_photos(self, owner_id: int, album_id: str = 'profile') -> List[Dict]:
        """
        Получение фотографий пользователя

        Args:
            owner_id: ID владельца фото
            album_id: ID альбома ('profile', 'wall' и т.д.)

        Returns:
            Список фотографий
        """
        params = {
            'owner_id': owner_id,
            'album_id': album_id,
            'extended': 1,
            'photo_sizes': 1
        }
        return self.call_method('photos.get', params).get('items', [])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()