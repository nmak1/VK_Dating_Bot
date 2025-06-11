import logging
from typing import Dict, Any, Optional
from vk_api.bot_longpoll import VkBotEventType
from config import constants
from core.vk_api.client import VKAPIClient
from core.db.repositories import UserRepository
from services.formatter import ProfileFormatter
from services.analyzer import InterestAnalyzer

logger = logging.getLogger(__name__)


class MessageHandler:
    def __init__(self, vk_client: VKAPIClient, user_repo: UserRepository):
        self.vk = vk_client
        self.user_repo = user_repo
        self.formatter = ProfileFormatter()
        self.analyzer = InterestAnalyzer()
        self.command_handlers = {
            "начать": self._handle_start,
            "привет": self._handle_start,
            "найти": self._handle_search,
            "избранные": self._handle_show_favorites,
            "черный список": self._handle_blacklist,
            "помощь": self._handle_help,
            "help": self._handle_help
        }

    async def handle(self, event: Dict[str, Any]) -> bool:
        """
        Основной метод обработки входящего сообщения

        Args:
            event: Словарь с данными события от VK

        Returns:
            bool: Успешность обработки сообщения
        """
        try:
            if event['type'] != VkBotEventType.MESSAGE_NEW:
                return False

            message = event['object']['message']
            user_id = message['from_id']
            text = message['text'].lower()

            # Обработка команды
            handler = self.command_handlers.get(text)
            if handler:
                return await handler(user_id)

            # Обработка произвольного текста
            return await self._handle_text_message(user_id, text)

        except Exception as e:
            logger.error(f"Message handling error: {e}", exc_info=True)
            return False

    async def _handle_start(self, user_id: int) -> bool:
        """Обработка команды начала работы"""
        keyboard = self.formatter.create_keyboard(keyboard_type="main")
        return await self.vk.send_message(
            user_id=user_id,
            message=constants.Messages.WELCOME,
            keyboard=keyboard
        )

    async def _handle_search(self, user_id: int) -> bool:
        """Обработка команды поиска"""
        # Получаем информацию о текущем пользователе
        current_user = self.vk.get_user_info(user_id)
        if not current_user:
            await self.vk.send_message(
                user_id=user_id,
                message="Не удалось получить ваши данные. Проверьте настройки приватности."
            )
            return False

        # Ищем совпадения
        matches = self.user_repo.find_matches(current_user)
        if not matches:
            await self.vk.send_message(
                user_id=user_id,
                message=constants.Messages.NO_MATCHES
            )
            return True

        # Показываем первое совпадение
        match = matches[0][1]
        profile_text = self.formatter.format_profile(match, current_user)
        photos = self.vk.get_top_photos(match['id'])
        keyboard = self.formatter.create_keyboard(
            keyboard_type="main",
            match_id=match['id'],
            photos=photos
        )

        return await self.vk.send_message(
            user_id=user_id,
            message=profile_text,
            attachment=photos,
            keyboard=keyboard
        )

    async def _handle_show_favorites(self, user_id: int) -> bool:
        """Обработка команды показа избранных"""
        favorites = self.user_repo.get_favorites(user_id)
        message = self.formatter.format_favorites(favorites)
        return await self.vk.send_message(
            user_id=user_id,
            message=message
        )

    async def _handle_blacklist(self, user_id: int) -> bool:
        """Обработка команды работы с черным списком"""
        blacklist = self.user_repo.get_blacklist(user_id)
        if not blacklist:
            message = "Ваш черный список пуст."
        else:
            users_info = self.vk.get_users_info(blacklist)
            message = "Черный список:\n" + "\n".join(
                f"{i + 1}. {user['first_name']} {user['last_name']}"
                for i, user in enumerate(users_info)
            )

        keyboard = self.formatter.create_keyboard(keyboard_type="confirm")
        return await self.vk.send_message(
            user_id=user_id,
            message=message,
            keyboard=keyboard
        )

    async def _handle_help(self, user_id: int) -> bool:
        """Обработка команды помощи"""
        help_text = (
            "Доступные команды:\n"
            "• Найти - начать поиск партнеров\n"
            "• Избранные - показать ваш список избранных\n"
            "• Черный список - управление черным списком\n"
            "• Помощь - показать это сообщение"
        )
        return await self.vk.send_message(
            user_id=user_id,
            message=help_text
        )

    async def _handle_text_message(self, user_id: int, text: str) -> bool:
        """Обработка произвольного текстового сообщения"""
        # Анализируем текст сообщения
        intent = self.analyzer.analyze_text(text)

        if intent == "greeting":
            return await self._handle_start(user_id)
        elif intent == "search":
            return await self._handle_search(user_id)
        else:
            return await self.vk.send_message(
                user_id=user_id,
                message="Не понимаю ваше сообщение. Напишите 'помощь' для списка команд."
            )