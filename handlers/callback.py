import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, validator
from vk_api.bot_longpoll import VkBotEventType
from config import constants
from core import ConfigurationError
from core.db.repositories import UserRepository
from core.vk_api.models.client import VKAPIClient
from services.formatter import ProfileFormatter

logger = logging.getLogger(__name__)


class CallbackPayload(BaseModel):
    """Модель payload данных callback"""
    command: str
    user_id: Optional[int] = None
    match_id: Optional[int] = None
    photo_id: Optional[str] = None
    favorite_id: Optional[int] = None

    @validator('command')
    def validate_command(cls, v):
        allowed_commands = [
            'show_next',
            'add_favorite',
            'like_photo',
            'confirm_yes',
            'confirm_no'
        ]
        if v not in allowed_commands:
            raise ValueError(f"Invalid command. Allowed: {allowed_commands}")
        return v


class CallbackHandler:
    def __init__(self, vk_client: VKAPIClient, user_repo: UserRepository):
        self.vk = vk_client
        self.user_repo = user_repo
        self.formatter = ProfileFormatter()

    async def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Основной метод обработки callback событий
        Args:
            event: Словарь с данными события от VK
        Returns:
            Словарь с результатом обработки или None при ошибке
        """
        try:
            if event.get('type') == 'confirmation':
                return self._handle_confirmation(event.get('group_id'))

            if event.get('type') == VkBotEventType.MESSAGE_EVENT.value:
                return await self._handle_message_event(event.get('object', {}))

            logger.warning(f"Unknown callback type: {event.get('type')}")
            return None

        except Exception as e:
            logger.error(f"Callback handling error: {e}", exc_info=True)
            return None

    async def _handle_message_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка событий от интерактивных элементов"""
        try:
            payload = self._parse_payload(event_data.get('payload'))
            user_id = event_data['user_id']

            handlers = {
                'show_next': self._handle_show_next,
                'add_favorite': self._handle_add_favorite,
                'like_photo': self._handle_like_photo,
                'confirm_yes': self._handle_confirm,
                'confirm_no': self._handle_reject
            }

            if payload.command in handlers:
                return await handlers[payload.command](user_id, payload)

            return {"result": "unknown_command"}

        except Exception as e:
            logger.error(f"Message event handling error: {e}", exc_info=True)
            return {"result": "error", "message": str(e)}

    def _parse_payload(self, payload: Any) -> CallbackPayload:
        """Парсинг и валидация payload"""
        if isinstance(payload, str):
            payload = json.loads(payload)
        return CallbackPayload(**payload)

    async def _handle_show_next(self, user_id: int, payload: CallbackPayload) -> Dict[str, Any]:
        """Обработка запроса показа следующего профиля"""
        if not payload.match_id:
            return {"result": "error", "message": "Missing match_id"}

        next_match = self.user_repo.get_next_match(user_id, payload.match_id)
        if not next_match:
            await self.vk.send_message(
                user_id=user_id,
                message=constants.Messages.NO_MATCHES
            )
            return {"result": "no_more_matches"}

        profile_text = self.formatter.format_profile(next_match)
        photos = self.vk.get_top_photos(next_match['id'])
        keyboard = self.formatter.create_keyboard(
            keyboard_type="main",
            match_id=next_match['id'],
            photos=photos
        )

        await self.vk.send_message(
            user_id=user_id,
            message=profile_text,
            attachment=photos,
            keyboard=keyboard
        )

        return {"result": "success"}

    async def _handle_add_favorite(self, user_id: int, payload: CallbackPayload) -> Dict[str, Any]:
        """Обработка добавления в избранное"""
        if not payload.favorite_id:
            return {"result": "error", "message": "Missing favorite_id"}

        success = self.user_repo.add_favorite(user_id, payload.favorite_id)
        if success:
            await self.vk.send_message(
                user_id=user_id,
                message=constants.Messages.FAVORITE_ADDED
            )
            return {"result": "success"}

        return {"result": "already_exists"}

    async def _handle_like_photo(self, user_id: int, payload: CallbackPayload) -> Dict[str, Any]:
        """Обработка лайка фотографии"""
        if not payload.photo_id:
            return {"result": "error", "message": "Missing photo_id"}

        success = await self.vk.like_photo(user_id, payload.photo_id)
        return {"result": "success" if success else "error"}

    async def _handle_confirm(self, user_id: int, payload: CallbackPayload) -> Dict[str, Any]:
        """Обработка подтверждающего действия"""
        await self.vk.send_message(
            user_id=user_id,
            message="Действие подтверждено"
        )
        return {"result": "confirmed"}

    async def _handle_reject(self, user_id: int, payload: CallbackPayload) -> Dict[str, Any]:
        """Обработка отклоняющего действия"""
        await self.vk.send_message(
            user_id=user_id,
            message="Действие отменено"
        )
        return {"result": "rejected"}

    def _handle_confirmation(self, group_id: int) -> Dict[str, Any]:
        """
        Обработка подтверждения сервера для Callback API VK

        Args:
            group_id: ID группы/сообщества, для которого требуется подтверждение

        Returns:
            Словарь с ответом для платформы, содержащий:
            - confirmation_code: строка подтверждения из настроек
            - group_id: ID группы (для верификации)
            - api_version: используемая версия API

        Raises:
            ConfigurationError: если код подтверждения не найден в настройках
        """
        try:
            # Получаем код подтверждения из настроек группы
            confirmation_code = self._get_confirmation_code(group_id)

            if not confirmation_code:
                raise ConfigurationError(
                    f"Confirmation code not found for group {group_id}. "
                    "Please check your group settings."
                )

            return {
                "response": {
                    "confirmation_code": confirmation_code,
                    "group_id": group_id,
                    "api_version": constants.VK_API_VERSION,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "status": "ok"
            }

        except Exception as e:
            logger.error(
                f"Failed to handle confirmation for group {group_id}: {str(e)}",
                exc_info=True,
                extra={"group_id": group_id}
            )
            raise

    def _get_confirmation_code(self, group_id: int) -> Optional[str]:
        """
        Получает код подтверждения для указанной группы

        Ищет код в следующем порядке:
        1. Кэш (если настроен)
        2. Настройки приложения
        3. Внешнее хранилище (если настроено)

        Returns:
            Строка с кодом подтверждения или None если не найден
        """
        # Реализация может использовать:
        # - self.settings
        # - self.cache
        # - Внешние API
        return self.settings.get(f"vk_groups.{group_id}.confirmation_code")