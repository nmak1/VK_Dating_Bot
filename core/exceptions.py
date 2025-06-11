from typing import Optional


class VKAPIError(Exception):
    """Базовое исключение для ошибок VK API"""
    def __init__(self, message: str, code: Optional[int] = None):
        self.code = code
        super().__init__(f"[VK API] {message} (code: {code})" if code else f"[VK API] {message}")

class ConfigurationError(VKAPIError):
    """Ошибка конфигурации"""
    def __init__(self, setting_key: str, group_id: Optional[int] = None):
        msg = f"Missing required configuration: {setting_key}"
        if group_id:
            msg += f" for group {group_id}"
        super().__init__(msg)

class APILimitError(VKAPIError):
    """Превышение лимитов API"""
    def __init__(self, retry_after: int):
        super().__init__(f"API limit exceeded. Retry after {retry_after} seconds")
        self.retry_after = retry_after

class InvalidRequestError(VKAPIError):
    """Некорректный запрос"""
    pass