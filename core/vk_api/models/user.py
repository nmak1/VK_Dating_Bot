from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class Gender(str, Enum):
    """Пол пользователя"""
    UNKNOWN = "unknown"
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class VkUser(BaseModel):
    """Основная модель пользователя VK"""
    id: int = Field(..., description="Уникальный идентификатор пользователя")
    first_name: str = Field(..., max_length=100, description="Имя пользователя")
    last_name: str = Field(..., max_length=100, description="Фамилия пользователя")
    domain: str = Field(..., description="Короткое имя страницы")
    sex: Gender = Field(default=Gender.UNKNOWN, description="Пол пользователя")
    bdate: Optional[str] = Field(None, description="Дата рождения в формате DD.MM.YYYY")
    city: Optional[Dict[str, Any]] = Field(None, description="Город пользователя")
    country: Optional[Dict[str, Any]] = Field(None, description="Страна пользователя")
    photo_max: Optional[str] = Field(None, description="URL фотографии максимального размера")
    online: Optional[bool] = Field(None, description="Статус онлайн")
    last_seen: Optional[datetime] = Field(None, description="Время последнего посещения")

    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> Optional[int]:
        """Возраст пользователя (вычисляется из bdate)"""
        if not self.bdate:
            return None
        try:
            parts = self.bdate.split('.')
            if len(parts) == 3:
                birth_date = datetime.strptime(self.bdate, "%d.%m.%Y")
                today = datetime.now()
                return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return None
        except Exception as e:
            logger.error(f"Error calculating age: {e}")
            return None


class VkGroup(BaseModel):
    """Модель группы VK"""
    id: int
    name: str
    screen_name: str
    is_closed: bool
    type: str
    photo_200: Optional[str] = None
    members_count: Optional[int] = None


class VkPhoto(BaseModel):
    """Модель фотографии VK"""
    id: int
    owner_id: int
    sizes: List[Dict[str, Any]]
    likes: Dict[str, Any] = Field(default_factory=dict)
    comments: Dict[str, Any] = Field(default_factory=dict)

    @property
    def max_size_url(self) -> Optional[str]:
        """URL фотографии максимального размера"""
        if not self.sizes:
            return None
        return max(self.sizes, key=lambda x: x['width'])['url']


class VkMessage(BaseModel):
    """Модель сообщения VK"""
    id: int
    from_id: int
    peer_id: int
    text: str
    date: datetime
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    payload: Optional[str] = None

    @validator('date', pre=True)
    def parse_date(cls, value):
        """Преобразует timestamp в datetime"""
        if isinstance(value, int):
            return datetime.fromtimestamp(value)
        return value


class VkConversation(BaseModel):
    """Модель беседы/диалога"""
    peer: Dict[str, Any]
    last_message_id: int
    unread_count: int


class VkGeo(BaseModel):
    """Геопозиция"""
    type: str
    coordinates: Dict[str, Any]
    place: Optional[Dict[str, Any]] = None


class VkLink(BaseModel):
    """Внешняя ссылка"""
    url: str
    title: str
    description: Optional[str] = None
    photo: Optional[Dict[str, Any]] = None


class VkError(BaseModel):
    """Модель ошибки VK API"""
    error_code: int
    error_msg: str
    request_params: List[Dict[str, Any]] = Field(default_factory=list)


class VkApiResponse(BaseModel):
    """Базовый ответ VK API"""
    response: Optional[Dict[str, Any]] = None
    error: Optional[VkError] = None


class VkUserSearchResult(BaseModel):
    """Результат поиска пользователей"""
    count: int
    items: List[VkUser]


class VkGroupSearchResult(BaseModel):
    """Результат поиска групп"""
    count: int
    items: List[VkGroup]


class VkMessageEvent(BaseModel):
    """Событие сообщения Callback API"""
    type: str
    object: Dict[str, Any]
    group_id: int

    @property
    def user_id(self) -> Optional[int]:
        """ID пользователя, отправившего сообщение"""
        return self.object.get('from_id')


class VkKeyboardButton(BaseModel):
    """Кнопка клавиатуры"""
    action: Dict[str, Any]
    color: Optional[str] = None


class VkKeyboard(BaseModel):
    """Клавиатура бота"""
    buttons: List[List[VkKeyboardButton]]
    inline: bool = True


class VkClientInfo(BaseModel):
    """Информация о клиенте"""
    button_actions: List[str]
    keyboard: bool
    inline_keyboard: bool
    carousel: bool
    lang_id: int


class VkLongPollServer(BaseModel):
    """Сервер для Long Poll соединения"""
    key: str
    server: str
    ts: int


class VkUploadResponse(BaseModel):
    """Ответ после загрузки файла"""
    server: int
    photo: str
    hash: str