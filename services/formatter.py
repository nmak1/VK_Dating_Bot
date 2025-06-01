from typing import Dict, List, Optional
from config import constants
from core.vk_api.models import VkUser
from services.analyzer import InterestAnalyzer
import json


class ProfileFormatter:
    def __init__(self):
        self.analyzer = InterestAnalyzer()
        self.photo_template = "photo{owner_id}_{photo_id}"

    def format_profile(self, user_data: Dict, compared_with: Optional[Dict] = None) -> str:
        """
        Форматирование профиля пользователя для вывода

        Args:
            user_data: Данные пользователя из VK API
            compared_with: Данные пользователя для сравнения (опционально)

        Returns:
            Отформатированная строка с информацией о профиле
        """
        try:
            user = VkUser(**user_data) if not isinstance(user_data, VkUser) else user_data
            common_interests = self._get_common_interests(user_data.get("compared_with", compared_with))

            return constants.Messages.PROFILE_TEMPLATE.format(
                name=f"{user.first_name} {user.last_name}",
                age=user.age or "не указан",
                city=user.city.get('title', 'не указан') if user.city else "не указан",
                link=f"https://vk.com/{user.domain}",
                common_interests=common_interests or "не найдено"
            )
        except Exception as e:
            print(f"Error formatting profile: {e}")
            return f"{user_data.get('first_name', 'Пользователь')} {user_data.get('last_name', '')}"

    def _get_common_interests(self, comparison_data: Optional[Dict]) -> str:
        """Вычисление общих интересов с другим пользователем"""
        if not comparison_data:
            return ""

        common = []
        for field in ['interests', 'music', 'books']:
            if comparison_data.get(field):
                common.extend(interest.strip() for interest in comparison_data[field].split(','))

        return ", ".join(set(filter(None, common))) if common else ""

    def format_photos(self, photos: List[Dict]) -> List[str]:
        """Форматирование списка фотографий для VK API"""
        return [
            self.photo_template.format(
                owner_id=photo['owner_id'],
                photo_id=photo['id']
            )
            for photo in sorted(
                photos,
                key=lambda x: x['likes']['count'],
                reverse=True
            )[:constants.BotConstants.MAX_PHOTOS]
        ]

    def format_search_results(self, results: List[Dict]) -> str:
        """Форматирование результатов поиска"""
        if not results:
            return constants.Messages.NO_MATCHES

        return "\n\n".join([
            f"{i + 1}. {self.format_profile(user)}"
            for i, (score, user) in enumerate(results[:5])
        ])

    def format_favorites(self, favorites: List[Dict]) -> str:
        """Форматирование списка избранных"""
        if not favorites:
            return "В избранном пока никого нет."

        return "\n\n".join([
            f"{i + 1}. {self.format_profile(fav)}\n"
            f"Добавлен: {fav['added_at'].strftime('%d.%m.%Y %H:%M')}"
            for i, fav in enumerate(favorites)
        ])

    def create_keyboard(self, user_id: int = None, match_id: int = None) -> Dict:
        """Создание интерактивной клавиатуры"""
        buttons = []

        if match_id:
            buttons.append([
                {
                    "action": {
                        "type": "callback",
                        "label": "❤️ В избранное",
                        "payload": json.dumps({
                            "command": "add_favorite",
                            "favorite_id": match_id
                        })
                    },
                    "color": "positive"
                },
                {
                    "action": {
                        "type": "callback",
                        "label": "➡️ Следующий",
                        "payload": json.dumps({
                            "command": "show_next",
                            "current_match_id": match_id
                        })
                    },
                    "color": "primary"
                }
            ])

        return {
            "inline": True,
            "buttons": buttons
        }