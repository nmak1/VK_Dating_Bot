from typing import Optional, Dict, Any
from vk_api.bot_longpoll import VkBotEventType
from pydantic import BaseModel
from config import constants
from core.vk_api.client import VKClient
from core.db.repositories import UserRepository
from services.formatter import format_profile


class CallbackData(BaseModel):
    """Модель данных callback-события"""
    type: str
    object: Dict[str, Any]
    group_id: int


class CallbackHandler:
    def __init__(self, vk_client: VKClient, user_repo: UserRepository):
        self.vk = vk_client
        self.user_repo = user_repo

    async def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обработка входящего callback-события"""
        try:
            callback = CallbackData(**event)

            if callback.type == VkBotEventType.MESSAGE_EVENT.value:
                return await self._handle_message_event(callback.object)
            elif callback.type == "confirmation":
                return self._handle_confirmation(callback.group_id)

        except Exception as e:
            print(f"Callback handling error: {e}")
            return None

    async def _handle_message_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка событий от кнопок"""
        user_id = event_data["user_id"]
        payload = event_data.get("payload", {})

        if payload.get("command") == "show_next":
            return await self._handle_show_next(user_id, payload)
        elif payload.get("command") == "add_favorite":
            return await self._handle_add_favorite(user_id, payload)
        elif payload.get("command") == "like_photo":
            return await self._handle_like_photo(user_id, payload)

        return {"result": "unknown_command"}

    async def _handle_show_next(self, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Показать следующего пользователя"""
        match_id = payload.get("current_match_id")
        if not match_id:
            return {"result": "error", "message": "No match ID provided"}

        next_match = self.user_repo.get_next_match(user_id, match_id)
        if not next_match:
            return {"result": "error", "message": "No more matches"}

        profile_text = format_profile(next_match)
        photos = self.vk.get_top_photos(next_match["id"])

        keyboard = self._create_action_keyboard(next_match["id"])

        await self.vk.send_message(
            user_id=user_id,
            message=profile_text,
            attachment=photos,
            keyboard=keyboard
        )

        return {"result": "success"}

    async def _handle_add_favorite(self, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Добавить в избранное"""
        favorite_id = payload.get("favorite_id")
        if not favorite_id:
            return {"result": "error", "message": "No favorite ID provided"}

        success = self.user_repo.add_favorite(user_id, favorite_id)
        if success:
            await self.vk.send_message(
                user_id=user_id,
                message=constants.Messages.FAVORITE_ADDED
            )
            return {"result": "success"}

        return {"result": "error", "message": "Already in favorites"}

    async def _handle_like_photo(self, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка лайка фото"""
        photo_id = payload.get("photo_id")
        if not photo_id:
            return {"result": "error", "message": "No photo ID provided"}

        success = self.vk.like_photo(user_id, photo_id)
        return {"result": "success" if success else "error"}

    def _handle_confirmation(self, group_id: int) -> Dict[str, Any]:
        """Обработка подтверждения сервера"""
        # Здесь должен быть ваш код подтверждения
        return {"response": "your_confirmation_code"}

    def _create_action_keyboard(self, match_id: int) -> Dict[str, Any]:
        """Создание клавиатуры с действиями"""
        return {
            "inline": True,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "callback",
                            "label": "❤️ В избранное",
                            "payload": {
                                "command": "add_favorite",
                                "favorite_id": match_id
                            }
                        },
                        "color": "positive"
                    },
                    {
                        "action": {
                            "type": "callback",
                            "label": "➡️ Следующий",
                            "payload": {
                                "command": "show_next",
                                "current_match_id": match_id
                            }
                        },
                        "color": "primary"
                    }
                ],
                [
                    {
                        "action": {
                            "type": "callback",
                            "label": "👍 Фото 1",
                            "payload": {
                                "command": "like_photo",
                                "photo_id": f"{match_id}_1"
                            }
                        },
                        "color": "secondary"
                    },
                    {
                        "action": {
                            "type": "callback",
                            "label": "👍 Фото 2",
                            "payload": {
                                "command": "like_photo",
                                "photo_id": f"{match_id}_2"
                            }
                        },
                        "color": "secondary"
                    },
                    {
                        "action": {
                            "type": "callback",
                            "label": "👍 Фото 3",
                            "payload": {
                                "command": "like_photo",
                                "photo_id": f"{match_id}_3"
                            }
                        },
                        "color": "secondary"
                    }
                ]
            ]
        }