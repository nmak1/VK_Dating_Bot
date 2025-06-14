from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn
from typing import Optional


class Settings(BaseSettings):
    POSTGRES_DB: str = Field(..., min_length=1)
    POSTGRES_USER: str = Field(..., min_length=1)
    POSTGRES_PASSWORD: str = Field(..., min_length=1)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    VK_GROUP_TOKEN: str = Field(..., min_length=85)
    VK_GROUP_ID: int = Field(..., gt=0)
    VK_USER_TOKEN: Optional[str] = Field(None, min_length=85)

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Игнорировать лишние переменные


try:
    settings = Settings()
except Exception as e:
    print(f"Ошибка загрузки настроек: {e}")
    print("Проверьте наличие и содержание .env файла")
    raise