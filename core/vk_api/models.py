from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class VkUser(BaseModel):
    """Базовая модель пользователя VK"""
    id: int
    first_name: str
    last_name: str
    domain: str
    bdate: Optional[str] = None
    sex: Optional[int] = None
    city: Optional[dict] = None
    interests: Optional[str] = None
    music: Optional[str] = None
    books: Optional[str] = None
    groups: Optional[dict] = None
    is_closed: Optional[bool] = None
    counters: Optional[dict] = None

    @property
    def age(self) -> Optional[int]:
        if not self.bdate:
            return None
        parts = self.bdate.split('.')
        if len(parts) == 3:
            birth_year = int(parts[2])
            return datetime.now().year - birth_year
        return None

    @property
    def city_id(self) -> Optional[int]:
        return self.city.get('id') if self.city else None

class VkPhoto(BaseModel):
    """Модель фотографии VK"""
    id: int
    owner_id: int
    likes: dict
    sizes: List[dict]

    @property
    def like_count(self) -> int:
        return self.likes.get('count', 0)

class VkSearchResult(BaseModel):
    """Результат поиска пользователей"""
    count: int
    items: List[VkUser]

class VkGroup(BaseModel):
    """Модель группы VK"""
    id: int
    name: str
    screen_name: str
    is_closed: int
    type: str
    photo_50: str
    photo_100: str
    photo_200: str