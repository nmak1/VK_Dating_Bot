from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from core.db.models import Favorite, Blacklist, PhotoLike, User, MatchViewHistory
from core.db.connector import get_session
from config import constants
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class UserRepository:
    """Репозиторий для работы с пользовательскими данными: избранное, черный список, лайки фото"""

    def __init__(self, session: Session = None):
        self.session = session or get_session()

    # === Работа с избранным ===
    def add_favorite(self, user_id: int, favorite_id: int) -> Tuple[bool, str]:
        """
        Добавление пользователя в избранное

        :param user_id: ID пользователя, который добавляет в избранное
        :param favorite_id: ID пользователя, которого добавляют
        :return: (success, message) - статус операции и сообщение
        """
        try:
            if user_id == favorite_id:
                return False, "Нельзя добавить себя в избранное"

            if self.is_favorite(user_id, favorite_id):
                return False, "Пользователь уже в избранном"

            favorite = Favorite(
                user_id=user_id,
                favorite_id=favorite_id,
                added_at=datetime.now()
            )
            self.session.add(favorite)
            self.session.commit()
            return True, "Пользователь добавлен в избранное"

        except Exception as e:
            logger.error(f"Error adding favorite: {e}", exc_info=True)
            self.session.rollback()
            return False, f"Ошибка при добавлении в избранное: {str(e)}"

    def remove_favorite(self, user_id: int, favorite_id: int) -> bool:
        """Удаление пользователя из избранного"""
        try:
            favorite = self.session.query(Favorite).filter_by(
                user_id=user_id,
                favorite_id=favorite_id
            ).first()

            if not favorite:
                return False

            self.session.delete(favorite)
            self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Error removing favorite: {e}", exc_info=True)
            self.session.rollback()
            return False

    def get_favorites(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получение списка избранных с пагинацией

        :param user_id: ID пользователя
        :param limit: количество записей
        :param offset: смещение
        :return: список словарей с информацией об избранных
        """
        try:
            favorites = self.session.query(Favorite).filter_by(
                user_id=user_id
            ).order_by(
                desc(Favorite.added_at)
            ).offset(offset).limit(limit).all()

            return [
                {
                    "user_id": fav.user_id,
                    "favorite_id": fav.favorite_id,
                    "added_at": fav.added_at.isoformat()
                }
                for fav in favorites
            ]
        except Exception as e:
            logger.error(f"Error getting favorites: {e}", exc_info=True)
            return []

    def count_favorites(self, user_id: int) -> int:
        """Получение количества избранных пользователей"""
        try:
            return self.session.query(Favorite).filter_by(user_id=user_id).count()
        except Exception as e:
            logger.error(f"Error counting favorites: {e}", exc_info=True)
            return 0

    def is_favorite(self, user_id: int, favorite_id: int) -> bool:
        """Проверка, есть ли пользователь в избранном"""
        try:
            return self.session.query(Favorite).filter_by(
                user_id=user_id,
                favorite_id=favorite_id
            ).first() is not None
        except Exception as e:
            logger.error(f"Error checking favorite: {e}", exc_info=True)
            return False

    # === Работа с черным списком ===
    def add_to_blacklist(self, user_id: int, banned_id: int) -> Tuple[bool, str]:
        """Добавление пользователя в черный список"""
        try:
            if user_id == banned_id:
                return False, "Нельзя добавить себя в черный список"

            if self.is_in_blacklist(user_id, banned_id):
                return False, "Пользователь уже в черном списке"

            blacklist = Blacklist(
                user_id=user_id,
                banned_id=banned_id,
                created_at=datetime.now()
            )
            self.session.add(blacklist)
            self.session.commit()
            return True, "Пользователь добавлен в черный список"

        except Exception as e:
            logger.error(f"Error adding to blacklist: {e}", exc_info=True)
            self.session.rollback()
            return False, f"Ошибка при добавлении в черный список: {str(e)}"

    def remove_from_blacklist(self, user_id: int, banned_id: int) -> bool:
        """Удаление пользователя из черного списка"""
        try:
            blacklist = self.session.query(Blacklist).filter_by(
                user_id=user_id,
                banned_id=banned_id
            ).first()

            if not blacklist:
                return False

            self.session.delete(blacklist)
            self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Error removing from blacklist: {e}", exc_info=True)
            self.session.rollback()
            return False

    def get_blacklist(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение черного списка с пагинацией"""
        try:
            blacklist = self.session.query(Blacklist).filter_by(
                user_id=user_id
            ).order_by(
                desc(Blacklist.created_at)
            ).offset(offset).limit(limit).all()

            return [
                {
                    "user_id": item.user_id,
                    "banned_id": item.banned_id,
                    "created_at": item.created_at.isoformat()
                }
                for item in blacklist
            ]
        except Exception as e:
            logger.error(f"Error getting blacklist: {e}", exc_info=True)
            return []

    def is_in_blacklist(self, user_id: int, banned_id: int) -> bool:
        """Проверка, находится ли пользователь в черном списке"""
        try:
            return self.session.query(Blacklist).filter_by(
                user_id=user_id,
                banned_id=banned_id
            ).first() is not None
        except Exception as e:
            logger.error(f"Error checking blacklist: {e}", exc_info=True)
            return False

    def count_blacklist(self, user_id: int) -> int:
        """Получение количества пользователей в черном списке"""
        try:
            return self.session.query(Blacklist).filter_by(user_id=user_id).count()
        except Exception as e:
            logger.error(f"Error counting blacklist: {e}", exc_info=True)
            return 0

    # === Работа с лайками фотографий ===
    def toggle_photo_like(self, user_id: int, photo_id: str) -> Tuple[bool, Optional[bool]]:
        """
        Переключение статуса лайка фотографии

        :return: (success, like_status) - статус операции и текущее состояние лайка
        """
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
                    liked=True,
                    created_at=datetime.now()
                )
                self.session.add(like)

            self.session.commit()
            return True, like.liked

        except Exception as e:
            logger.error(f"Error toggling photo like: {e}", exc_info=True)
            self.session.rollback()
            return False, None

    def get_photo_likes(self, user_id: int) -> Dict[str, bool]:
        """Получение всех лайков фотографий пользователя"""
        try:
            likes = self.session.query(PhotoLike).filter_by(
                user_id=user_id
            ).all()

            return {like.photo_id: like.liked for like in likes}
        except Exception as e:
            logger.error(f"Error getting photo likes: {e}", exc_info=True)
            return {}

    def count_photo_likes(self, user_id: int) -> int:
        """Получение количества лайков фотографий пользователя"""
        try:
            return self.session.query(PhotoLike).filter_by(
                user_id=user_id,
                liked=True
            ).count()
        except Exception as e:
            logger.error(f"Error counting photo likes: {e}", exc_info=True)
            return 0

    # === Работа с историей просмотров ===
    def add_to_view_history(self, user_id: int, viewed_user_id: int) -> bool:
        """Добавление пользователя в историю просмотров"""
        try:
            if user_id == viewed_user_id:
                return False

            # Проверяем, есть ли уже такая запись
            existing = self.session.query(MatchViewHistory).filter_by(
                user_id=user_id,
                viewed_user_id=viewed_user_id
            ).first()

            if existing:
                existing.viewed_at = datetime.now()
            else:
                view = MatchViewHistory(
                    user_id=user_id,
                    viewed_user_id=viewed_user_id,
                    viewed_at=datetime.now()
                )
                self.session.add(view)

            self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Error adding to view history: {e}", exc_info=True)
            self.session.rollback()
            return False

    def get_view_history(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение истории просмотренных профилей"""
        try:
            history = self.session.query(MatchViewHistory).filter_by(
                user_id=user_id
            ).order_by(
                desc(MatchViewHistory.viewed_at)
            ).offset(offset).limit(limit).all()

            return [
                {
                    "viewed_user_id": item.viewed_user_id,
                    "viewed_at": item.viewed_at.isoformat()
                }
                for item in history
            ]
        except Exception as e:
            logger.error(f"Error getting view history: {e}", exc_info=True)
            return []

    def clear_view_history(self, user_id: int) -> bool:
        """Очистка истории просмотров"""
        try:
            self.session.query(MatchViewHistory).filter_by(
                user_id=user_id
            ).delete()

            self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Error clearing view history: {e}", exc_info=True)
            self.session.rollback()
            return False

    # === Взаимные действия ===
    def get_mutual_favorites(self, user_id: int) -> List[int]:
        """Получение списка взаимных избранных (кто добавил меня и я его)"""
        try:
            # Пользователи, которых я добавил в избранное
            my_favorites = {f.favorite_id for f in
                            self.session.query(Favorite).filter_by(user_id=user_id).all()}

            # Пользователи, которые добавили меня в избранное
            favorited_me = {f.user_id for f in
                            self.session.query(Favorite).filter_by(favorite_id=user_id).all()}

            return list(my_favorites & favorited_me)

        except Exception as e:
            logger.error(f"Error getting mutual favorites: {e}", exc_info=True)
            return []

    def get_mutual_likes(self, user_id: int) -> List[int]:
        """Получение списка пользователей с взаимными лайками фото"""
        # Здесь должна быть более сложная логика анализа лайков
        return []

    # === Поиск и рекомендации ===
    def get_next_match(self, user_id: int, current_match_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Получение следующего подходящего пользователя"""
        try:
            # Получаем черный список и избранное
            blacklist = {item.banned_id for item in
                         self.session.query(Blacklist).filter_by(user_id=user_id).all()}

            favorites = {item.favorite_id for item in
                         self.session.query(Favorite).filter_by(user_id=user_id).all()}

            viewed_users = {item.viewed_user_id for item in
                            self.session.query(MatchViewHistory).filter_by(user_id=user_id).all()}

            # Исключаем себя, черный список, избранное и уже просмотренных
            excluded_users = blacklist | favorites | viewed_users | {user_id}

            # Здесь должна быть логика поиска следующего пользователя
            # Например, через внешний API или сложный запрос к базе

            # Заглушка - просто берем случайного пользователя
            next_user = self.session.query(User).filter(
                User.id.notin_(excluded_users)
            ).order_by(func.random()).first()

            if not next_user:
                return None

            # Добавляем в историю просмотров
            self.add_to_view_history(user_id, next_user.id)

            return {
                "user_id": next_user.id,
                "name": next_user.name,
                "age": next_user.age,
                # другие поля
            }

        except Exception as e:
            logger.error(f"Error getting next match: {e}", exc_info=True)
            return None

    def close(self):
        """Закрытие сессии"""
        try:
            if self.session:
                self.session.close()
        except Exception as e:
            logger.error(f"Error closing session: {e}", exc_info=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()