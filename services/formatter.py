import json
from typing import Dict, List, Optional, Union
from datetime import datetime
from config import constants
from core.vk_api.models import VkUser
from services.analyzer import InterestAnalyzer
import logging

logger = logging.getLogger(__name__)


class ProfileFormatter:
    """Класс для форматирования данных профилей и сообщений бота"""

    def __init__(self):
        self.analyzer = InterestAnalyzer()
        self.photo_template = "photo{owner_id}_{photo_id}"

    def format_profile(
            self,
            user_data: Union[Dict, VkUser],
            current_user_data: Optional[Dict] = None,
            show_common_interests: bool = True
    ) -> str:
        """
        Форматирует данные профиля в читаемый текст

        Args:
            user_data: Данные профиля (словарь или объект VkUser)
            current_user_data: Данные текущего пользователя для сравнения
            show_common_interests: Показывать ли общие интересы

        Returns:
            Отформатированная строка с информацией о профиле
        """
        try:
            user = VkUser(**user_data) if not isinstance(user_data, VkUser) else user_data
            common_interests = ""

            if show_common_interests and current_user_data:
                common_interests = self._get_common_interests(user_data, current_user_data)
                common_interests = f"\nОбщие интересы: {common_interests}" if common_interests else ""

            city_name = user.city.get('title') if user.city else "не указан"
            age = user.age or "не указан"

            return constants.Messages.PROFILE_TEMPLATE.format(
                name=f"{user.first_name} {user.last_name}",
                age=age,
                city=city_name,
                link=f"https://vk.com/{user.domain}",
                common_interests=common_interests
            )
        except Exception as e:
            logger.error(f"Error formatting profile: {e}")
            return f"{user_data.get('first_name', 'Пользователь')} {user_data.get('last_name', '')}"

    def _get_common_interests(
            self,
            profile1: Union[Dict, VkUser],
            profile2: Union[Dict, VkUser]
    ) -> str:
        """Находит и форматирует общие интересы между двумя профилями"""
        try:
            fields_to_compare = ['interests', 'music', 'books', 'groups']
            common = []

            for field in fields_to_compare:
                data1 = getattr(profile1, field, None) if isinstance(profile1, VkUser) else profile1.get(field)
                data2 = getattr(profile2, field, None) if isinstance(profile2, VkUser) else profile2.get(field)

                if data1 and data2:
                    if field == 'groups':
                        common.extend(self._compare_groups(data1, data2))
                    else:
                        common.extend(self.analyzer.find_common_items(data1, data2))

            return ", ".join(set(filter(None, common))) if common else ""
        except Exception as e:
            logger.error(f"Error finding common interests: {e}")
            return ""

    def _compare_groups(self, groups1: List[Dict], groups2: List[Dict]) -> List[str]:
        """Сравнивает группы двух пользователей"""
        group_ids1 = {g['id'] for g in groups1}
        group_ids2 = {g['id'] for g in groups2}
        common_ids = group_ids1 & group_ids2

        common_groups = []
        for group in groups1 + groups2:
            if group['id'] in common_ids and group['name'] not in common_groups:
                common_groups.append(group['name'])

        return common_groups

    def format_photos(self, photos: List[Dict]) -> List[str]:
        """Форматирует фотографии для отправки через VK API"""
        try:
            sorted_photos = sorted(
                photos,
                key=lambda x: x['likes']['count'],
                reverse=True
            )[:constants.BotConstants.MAX_PHOTOS]

            return [
                self.photo_template.format(
                    owner_id=photo['owner_id'],
                    photo_id=photo['id']
                )
                for photo in sorted_photos
            ]
        except Exception as e:
            logger.error(f"Error formatting photos: {e}")
            return []

    def format_search_results(
            self,
            results: List[Dict],
            current_user_data: Optional[Dict] = None
    ) -> str:
        """Форматирует результаты поиска для отображения"""
        if not results:
            return constants.Messages.NO_MATCHES

        formatted_results = []
        for i, (score, user) in enumerate(results[:5], 1):
            profile = self.format_profile(user, current_user_data)
            formatted_results.append(f"{i}. {profile} (совпадение: {score:.0%})")

        return "\n\n".join(formatted_results)

    def format_favorites(self, favorites: List[Dict]) -> str:
        """Форматирует список избранных"""
        if not favorites:
            return "В избранном пока никого нет."

        formatted = []
        for i, fav in enumerate(favorites, 1):
            profile = self.format_profile(fav, show_common_interests=False)
            added_at = fav['added_at'].strftime('%d.%m.%Y %H:%M')
            formatted.append(f"{i}. {profile}\nДобавлен: {added_at}")

        return "\n\n".join(formatted)

    def create_keyboard(
            self,
            keyboard_type: str = "main",
            match_id: Optional[int] = None,
            photos: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Создает интерактивную клавиатуру для бота

        Args:
            keyboard_type: Тип клавиатуры (main, photos, confirm)
            match_id: ID текущего совпадения (для callback)
            photos: Список фотографий (для кнопок лайков)
        """
        keyboard = {"inline": True, "buttons": []}

        if keyboard_type == "main" and match_id:
            keyboard["buttons"].append([
                self._create_button(
                    "❤️ В избранное",
                    "add_favorite",
                    {"favorite_id": match_id}
                ),
                self._create_button(
                    "➡️ Следующий",
                    "show_next",
                    {"current_match_id": match_id}
                )
            ])

        if keyboard_type == "photos" and photos and match_id:
            photo_buttons = []
            for i, photo in enumerate(photos[:3], 1):
                photo_buttons.append(
                    self._create_button(
                        f"❤️ Фото {i}",
                        "like_photo",
                        {"photo_id": f"{match_id}_{i}"},
                        "secondary"
                    )
                )
            keyboard["buttons"].append(photo_buttons)

        if keyboard_type == "confirm":
            keyboard["buttons"].append([
                self._create_button("Да", "confirm_yes", {}, "positive"),
                self._create_button("Нет", "confirm_no", {}, "negative")
            ])

        return keyboard

    def _create_button(
            self,
            label: str,
            command: str,
            payload: Dict,
            color: str = "primary"
    ) -> Dict:
        """Создает одну кнопку для клавиатуры"""
        return {
            "action": {
                "type": "callback",
                "label": label,
                "payload": json.dumps({"command": command, **payload})
            },
            "color": color
        }

    def format_error_message(self, error: Exception) -> str:
        """Форматирует сообщение об ошибке для пользователя"""
        return "Произошла ошибка. Пожалуйста, попробуйте позже."