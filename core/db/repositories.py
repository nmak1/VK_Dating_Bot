from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from core.db.models import Favorite, Blacklist, PhotoLike
from core.db.connector import get_session
from config import constants
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """Репозиторий для работы с пользовательскими данными"""

    def __init__(self, session: Session = None):
        self.session = session or get_session()

    # === Работа с избранным ===
    def add_favorite(self, user_id: int, favorite_id: int) -> bool:
        """Добавление пользователя в избранное"""
        try:
            if not self.session.query(Favorite).filter_by(
                    user_id=user_id,
                    favorite_id=favorite_id
            ).first():
                favorite = Favorite(
                    user_id=user_id,
                    favorite_id=favorite_id,
                    added_at=datetime.now()
                )
                self.session.add(favorite)
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding favorite: {e}")
            self.session.rollback()
            return False

    def remove_favorite(self, user_id: int, favorite_id: int) -> bool:
        """Удаление пользователя из избранного"""
        try:
            favorite = self.session.query(Favorite).filter_by(
                user_id=user_id,
                favorite_id=favorite_id
            ).first()

            if favorite:
                self.session.delete(favorite)
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing favorite: {e}")
            self.session.rollback()
            return False

    def get_favorites(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение списка избранных"""
        try:
            favorites = self.session.query(Favorite).filter_by(
                user_id=user_id
            ).order_by(
                desc(Favorite.added_at)
            ).limit(limit).all()

            return [
                {
                    "user_id": fav.user_id,
                    "favorite_id": fav.favorite_id,
                    "added_at": fav.added_at
                }
                for fav in favorites
            ]
        except Exception as e:
            logger.error(f"Error getting favorites: {e}")
            return []

    def is_favorite(self, user_id: int, favorite_id: int) -> bool:
        """Проверка, есть ли пользователь в избранном"""
        try:
            return self.session.query(Favorite).filter_by(
                user_id=user_id,
                favorite_id=favorite_id
            ).first() is not None
        except Exception as e:
            logger.error(f"Error checking favorite: {e}")
            return False

    # === Работа с черным списком ===
    def add_to_blacklist(self, user_id: int, banned_id: int) -> bool:
        """Добавление пользователя в черный список"""
        try:
            if not self.session.query(Blacklist).filter_by(
                    user_id=user_id,
                    banned_id=banned_id
            ).first():
                blacklist = Blacklist(
                    user_id=user_id,
                    banned_id=banned_id
                )
                self.session.add(blacklist)
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding to blacklist: {e}")
            self.session.rollback()
            return False

    def remove_from_blacklist(self, user_id: int, banned_id: int) -> bool:
        """Удаление пользователя из черного списка"""
        try:
            blacklist = self.session.query(Blacklist).filter_by(
                user_id=user_id,
                banned_id=banned_id
            ).first()

            if blacklist:
                self.session.delete(blacklist)
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing from blacklist: {e}")
            self.session.rollback()
            return False

    def get_blacklist(self, user_id: int) -> List[int]:
        """Получение черного списка"""
        try:
            blacklist = self.session.query(Blacklist).filter_by(
                user_id=user_id
            ).all()

            return [item.banned_id for item in blacklist]
        except Exception as e:
            logger.error(f"Error getting blacklist: {e}")
            return []

    # === Работа с лайками фотографий ===
    def toggle_photo_like(self, user_id: int, photo_id: str) -> bool:
        """Переключение статуса лайка фотографии"""
        try:
            like = self.session.query(PhotoLike).filter_by(
                user_id=user_id,
                photo_id=photo_id
            ).first()

            if like:
                like.liked = not like.liked
                like.updated_at = datetime.now()
            else:
                like = PhotoLike(
                    user_id=user_id,
                    photo_id=photo_id,
                    liked=True
                )
                self.session.add(like)

            self.session.commit()
            return like.liked
        except Exception as e:
            logger.error(f"Error toggling photo like: {e}")
            self.session.rollback()
            return False

    def get_photo_likes(self, user_id: int) -> Dict[str, bool]:
        """Получение всех лайков фотографий пользователя"""
        try:
            likes = self.session.query(PhotoLike).filter_by(
                user_id=user_id
            ).all()

            return {like.photo_id: like.liked for like in likes}
        except Exception as e:
            logger.error(f"Error getting photo likes: {e}")
            return {}

    # === Поиск и рекомендации ===
    def get_next_match(self, user_id: int, current_match_id: int) -> Optional[Dict[str, Any]]:
        """Получение следующего подходящего пользователя"""
        try:
            # Получаем черный список и избранное
            blacklist = self.get_blacklist(user_id)
            favorites = [fav["favorite_id"] for fav in self.get_favorites(user_id)]

            # Ищем следующего пользователя, которого еще не показывали
            # Здесь должна быть более сложная логика поиска
            # В реальной реализации нужно интегрировать с VK API

            return None  # Заглушка для примера
        except Exception as e:
            logger.error(f"Error getting next match: {e}")
            return None

    def get_match_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение истории просмотренных профилей"""
        # В реальной реализации нужно хранить историю просмотров
        return []

    def close(self):
        """Закрытие сессии"""
        try:
            self.session.close()
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()