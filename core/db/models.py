from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional

Base = declarative_base()

class Favorite(Base):
    """Модель для хранения избранных пользователей"""
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    favorite_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_mutual = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="favorites_added")
    favorite_user = relationship("User", foreign_keys=[favorite_id], back_populates="favorites_received")

    def __repr__(self):
        return f"<Favorite(user_id={self.user_id}, favorite_id={self.favorite_id}, is_mutual={self.is_mutual})>"

class Blacklist(Base):
    """Модель для черного списка"""
    __tablename__ = 'blacklist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    banned_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="blacklists_created")
    banned_user = relationship("User", foreign_keys=[banned_id], back_populates="blacklists_received")

    def __repr__(self):
        return f"<Blacklist(user_id={self.user_id}, banned_id={self.banned_id}, created_at={self.created_at})>"

class PhotoLike(Base):
    """Модель для лайков фотографий"""
    __tablename__ = 'photo_likes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    photo_id = Column(String(36), nullable=False)  # UUID обычно 36 символов
    liked = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="photo_likes")

    # Composite index
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<PhotoLike(user_id={self.user_id}, photo_id={self.photo_id}, liked={self.liked})>"

class MatchViewHistory(Base):
    """Модель истории просмотров профилей"""
    __tablename__ = 'match_view_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    viewed_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String(50), nullable=True)  # Откуда пришел просмотр

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="view_history")
    viewed_user = relationship("User", foreign_keys=[viewed_user_id])

    # Composite index для быстрого поиска
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<MatchViewHistory(user_id={self.user_id}, viewed_user_id={self.viewed_user_id}, viewed_at={self.viewed_at})>"

class User(Base):
    """Модель пользователя (добавлена для связей)"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    # Другие поля пользователя...

    # Relationships
    favorites_added = relationship("Favorite", foreign_keys=[Favorite.user_id], back_populates="user")
    favorites_received = relationship("Favorite", foreign_keys=[Favorite.favorite_id], back_populates="favorite_user")
    blacklists_created = relationship("Blacklist", foreign_keys=[Blacklist.user_id], back_populates="user")
    blacklists_received = relationship("Blacklist", foreign_keys=[Blacklist.banned_id], back_populates="banned_user")
    photo_likes = relationship("PhotoLike", back_populates="user")
    view_history = relationship("MatchViewHistory", foreign_keys=[MatchViewHistory.user_id], back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id})>"