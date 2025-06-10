import pytest
from unittest.mock import MagicMock, patch
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from datetime import datetime
from core.bot_core import DatingBot
from core.db.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope='session')
def test_db():
    """Фикстура для тестовой PostgreSQL базы (сессионная)"""
    # Создаем временную тестовую БД
    original_db_name = "test_dating_bot_temp"
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {original_db_name}")
            cursor.execute(f"CREATE DATABASE {original_db_name}")
    finally:
        conn.close()

    # Подключаемся к тестовой БД
    test_conn = psycopg2.connect(
        dbname=original_db_name,
        user="postgres",
        password="postgres",
        host="localhost"
    )

    # Создаем таблицы
    engine = create_engine(f"postgresql+psycopg2://postgres:postgres@localhost/{original_db_name}")
    Base.metadata.create_all(engine)

    yield test_conn

    # Очистка после тестов
    test_conn.close()
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cursor:
        cursor.execute(f"DROP DATABASE {original_db_name}")
    conn.close()


@pytest.fixture
def db_session(test_db):
    """Фикстура для тестовой сессии SQLAlchemy"""
    engine = create_engine(f"postgresql+psycopg2://postgres:postgres@localhost/test_dating_bot_temp")
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Откатываем транзакции после каждого теста
    session.rollback()
    session.close()


@pytest.fixture
def mock_vk_api(mocker):
    """Фикстура для мока VK API"""
    mock = MagicMock()
    mocker.patch('vk_api.VkApi', return_value=mock)
    mock.get_api.return_value = MagicMock()
    return mock


@pytest.fixture
def mock_bot(mocker, mock_vk_api, db_session):
    """Фикстура для тестового бота с моками"""
    # Мокаем зависимости базы данных
    mocker.patch('core.db.connector.Database.get_session', return_value=db_session)

    # Создаем экземпляр бота с тестовыми параметрами
    bot = DatingBot()

    # Настраиваем моки для компонентов бота
    bot.vk = MagicMock()
    bot.user_vk = MagicMock()
    bot.matcher = MagicMock()
    bot.handler = MagicMock()

    # Стандартные ответы для методов VK API
    bot.user_vk.get_user_info.return_value = {
        'id': 123,
        'first_name': 'Test',
        'last_name': 'User',
        'bdate': '01.01.1990',
        'sex': 2,
        'city': {'id': 1},
        'interests': 'music,books',
        'is_closed': False,
        'domain': 'testuser'
    }

    bot.vk.search_users.return_value = {
        'count': 1,
        'items': [{
            'id': 456,
            'first_name': 'Match',
            'last_name': 'User',
            'bdate': '01.01.1992',
            'sex': 1,
            'city': {'id': 1},
            'interests': 'music',
            'is_closed': False,
            'domain': 'matchuser'
        }]
    }

    bot.vk.get_top_photos.return_value = [
        'photo456_1',
        'photo456_2',
        'photo456_3'
    ]

    return {
        'bot': bot,
        'mock_vk': bot.vk,
        'mock_user_vk': bot.user_vk,
        'mock_matcher': bot.matcher,
        'mock_handler': bot.handler,
        'db_session': db_session
    }


@pytest.fixture
def sample_user_data():
    """Фикстура с тестовыми данными пользователя"""
    return {
        'id': 123,
        'first_name': 'Test',
        'last_name': 'User',
        'bdate': '01.01.1990',
        'age': 33,
        'sex': 2,
        'city': {'id': 1, 'title': 'Moscow'},
        'interests': 'music,programming',
        'music': 'rock,classical',
        'books': 'sci-fi,fantasy',
        'groups': [],
        'domain': 'testuser',
        'is_closed': False
    }


@pytest.fixture
def sample_match_data():
    """Фикстура с тестовыми данными совпадения"""
    return {
        'id': 456,
        'first_name': 'Match',
        'last_name': 'User',
        'bdate': '01.01.1992',
        'age': 31,
        'sex': 1,
        'city': {'id': 1, 'title': 'Moscow'},
        'interests': 'music,travel',
        'domain': 'matchuser',
        'is_closed': False
    }


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Фикстура для мока переменных окружения"""
    monkeypatch.setenv('POSTGRES_DB', 'test_dating_bot_temp')
    monkeypatch.setenv('POSTGRES_USER', 'postgres')
    monkeypatch.setenv('POSTGRES_PASSWORD', 'postgres')
    monkeypatch.setenv('POSTGRES_HOST', 'localhost')
    monkeypatch.setenv('POSTGRES_PORT', '5432')
    monkeypatch.setenv('VK_GROUP_TOKEN', 'test_group_token')
    monkeypatch.setenv('VK_GROUP_ID', '12345')
    monkeypatch.setenv('VK_USER_TOKEN', 'test_user_token')