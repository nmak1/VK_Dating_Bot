from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class BaseEvent(BaseModel):
    type: str
    group_id: int
    event_id: str
    v: str


class ConfirmationEvent(BaseEvent):
    """Событие подтверждения сервера"""
    type: str = "confirmation"


class MessageEvent(BaseEvent):
    """Событие сообщения"""
    type: str = "message_new"
    object: Dict[str, Any]

    @property
    def user_id(self) -> int:
        return self.object.get('from_id')

    @property
    def text(self) -> str:
        return self.object.get('text', '')


class EventResponse(BaseModel):
    """Модель ответа на событие"""
    response: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None