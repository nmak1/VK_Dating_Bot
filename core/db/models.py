from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Favorite(Base):
    """Модель для хранения избранных пользователей"""
    __tablename__ = 'favorites'

    user_id = Column(Integer, primary_key=True)
    favorite_id = Column(Integer, primary_key=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Favorite(user_id={self.user_id}, favorite_id={self.favorite_id})>"

class Blacklist(Base):
    """Модель для черного списка"""
    __tablename__ = 'blacklist'

    user_id = Column(Integer, primary_key=True)
    banned_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return f"<Blacklist(user_id={self.user_id}, banned_id={self.banned_id})>"

class PhotoLike(Base):
    """Модель для лайков фотографий"""
    __tablename__ = 'photo_likes'

    user_id = Column(Integer, primary_key=True)
    photo_id = Column(String, primary_key=True)
    liked = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PhotoLike(user_id={self.user_id}, photo_id={self.photo_id}, liked={self.liked})>"