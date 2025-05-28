import pytest
from unittest.mock import MagicMock
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from datetime import datetime
from bot import VKAdvancedDatingBot  # изменённый импорт

@pytest.fixture
def mock_vk_api(mocker):
    mock = MagicMock()
    mocker.patch('vk_api.VkApi', return_value=mock)
    return mock

@pytest.fixture
def mock_bot(mocker, mock_vk_api):
    mocker.patch('bot.psycopg2.connect')  # изменённый путь
    bot = VKAdvancedDatingBot('group_token', 12345)
    bot.vk_user = MagicMock()
    return bot


@pytest.fixture(scope='session')
def postgresql():
    """Фикстура для тестовой PostgreSQL базы"""
    conn = psycopg2.connect(
        dbname=os.getenv('TEST_POSTGRES_DB', 'test_dating_bot'),
        user=os.getenv('TEST_POSTGRES_USER', 'postgres'),
        password=os.getenv('TEST_POSTGRES_PASSWORD', 'postgres'),
        host=os.getenv('TEST_POSTGRES_HOST', 'localhost'),
        port=os.getenv('TEST_POSTGRES_PORT', '5432')
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    with conn.cursor() as cursor:
        cursor.execute("DROP DATABASE IF EXISTS test_dating_bot")
        cursor.execute("CREATE DATABASE test_dating_bot")

    conn.close()

    test_conn = psycopg2.connect(
        dbname='test_dating_bot',
        user='postgres',
        password='postgres',
        host='localhost'
    )

    yield test_conn
    test_conn.close()


@pytest.fixture
def db_connection(postgresql):
    """Фикстура для подключения к тестовой базе"""
    with postgresql.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id BIGINT,
                favorite_id BIGINT,
                added_at TIMESTAMP,
                PRIMARY KEY (user_id, favorite_id)
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                user_id BIGINT,
                banned_id BIGINT,
                PRIMARY KEY (user_id, banned_id)
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photo_likes (
                user_id BIGINT,
                photo_id TEXT,
                liked BOOLEAN,
                PRIMARY KEY (user_id, photo_id)
            )
        ''')
        postgresql.commit()

    yield postgresql

    with postgresql.cursor() as cursor:
        cursor.execute('TRUNCATE TABLE favorites, blacklist, photo_likes')
        postgresql.commit()