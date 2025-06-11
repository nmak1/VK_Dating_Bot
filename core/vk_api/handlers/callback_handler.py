import logging
from typing import Dict, Any, Optional
from datetime import datetime
from ..models.events import ConfirmationEvent, MessageEvent, EventResponse
from ...exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class VKCallbackHandler:
    def __init__(self, settings: Dict[str, Any], api_client):
        self.settings = settings
        self.api_client = api_client

    def _get_confirmation_code(self, group_id: int) -> str:
        """Получает код подтверждения из настроек"""
        code = self.settings.get('vk', {}).get('groups', {}).get(str(group_id), {}).get('confirmation_code')
        if not code:
            raise ConfigurationError(f"vk.groups.{group_id}.confirmation_code", group_id)
        return code

    def _handle_confirmation(self, group_id: int) -> Dict[str, Any]:
        """Обработка подтверждения сервера"""
        code = self._get_confirmation_code(group_id)
        return {
            "response": {
                "confirmation_code": code,
                "group_id": group_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    def _handle_message(self, event: MessageEvent) -> EventResponse:
        """Обработка входящего сообщения"""
        try:
            # Здесь логика обработки сообщения
            return EventResponse(response={"status": "ok"})
        except Exception as e:
            logger.error(f"Message handling error: {str(e)}", exc_info=True)
            return EventResponse(error={"code": 500, "message": str(e)})

    def handle_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Основной обработчик событий"""
        try:
            event_type = event_data.get('type')

            if event_type == "confirmation":
                event = ConfirmationEvent(**event_data)
                return self._handle_confirmation(event.group_id)

            elif event_type == "message_new":
                event = MessageEvent(**event_data)
                return self._handle_message(event).dict()

            return {"response": "ok"}  # Для других типов событий

        except Exception as e:
            logger.error(f"Event handling failed: {str(e)}", exc_info=True)
            return {"error": {"code": 500, "message": str(e)}}