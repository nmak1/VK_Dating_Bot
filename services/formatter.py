from typing import Dict, Optional, List

from pydantic import json

from config import constants
from core.vk_api.models import VkUser
from services.analyzer import InterestAnalyzer


class ProfileFormatter:
    def __init__(self):
        self.analyzer = InterestAnalyzer()
        self.photo_template = "photo{owner_id}_{photo_id}"

    def format_profile(self, user_data: Dict) -> str:
        """Форматирование профиля пользователя для вывода"""
        user = VkUser(**user_data) if not isinstance(user_data, VkUser) else user_data

        common_interests = self._get_common_interests(user_data.get("compared_with"))
        city_name = user.city.get('title') if user.city else "не указан"

        return constants.Messages.PROFILE_TEMPLATE.format(
            name=f"{user.first_name} {user.last_name}",
            age=user.age or "не указан",
            city=city_name,
            link=f"https://vk.com/{user.domain}",
            common_interests=common_interests or "не найдено"
        )

    def format_photos(self, photos: List[Dict]) -> List[str]:
        """Форматирование списка фотографий"""
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

    def _get_common_interests(self, comparison_data: Optional[Dict]) -> str:
        """Получение общих интересов"""
        if not comparison_data:
            return ""

        common = []
        for field in ['interests', 'music', 'books']:
            if comparison_data.get(field):
                common.extend(comparison_data[field].split(','))

        return ", ".join(set(filter(None, common))) if common else ""

    def format_favorites(self, favorites: List[Dict]) -> str:
        """Форматирование списка избранных"""
        if not favorites:
            return "В избранном пока никого нет."

        return "\n\n".join([
            f"{i + 1}. {self.format_profile(fav)}\n"
            f"Добавлен: {fav['added_at'].strftime('%d.%m.%Y %H:%M')}"
            for i, fav in enumerate(favorites)
        ])

    def create_keyboard(self, user_id: int) -> Dict:
        """Создание клавиатуры для сообщения"""
        return {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "❤️ В избранное",
                            "payload": json.dumps({"user_id": user_id})
                        },
                        "color": "positive"
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "➡️ Следующий",
                            "payload": json.dumps({"command": "next"})
                        },
                        "color": "primary"
                    }
                ]
            ]
        }