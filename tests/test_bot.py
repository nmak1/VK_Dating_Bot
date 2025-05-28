from unittest.mock import MagicMock


class TestVKAdvancedDatingBot:
    def test_init(self, mock_bot):
        assert mock_bot is not None
        assert mock_bot.vk_group is not None
        assert mock_bot.longpoll is not None
        assert mock_bot.db_conn is not None

    def test_create_keyboards(self, mock_bot):
        assert hasattr(mock_bot, 'main_keyboard')
        assert hasattr(mock_bot, 'photo_keyboard')
        assert hasattr(mock_bot, 'confirm_keyboard')

    def test_get_user_info(self, mock_bot):
        mock_response = [{
            'id': 123,
            'first_name': 'Test',
            'last_name': 'User',
            'bdate': '01.01.1990',
            'sex': 2,
            'city': {'id': 1},
            'interests': 'music, books',
            'music': 'rock, jazz',
            'books': 'sci-fi',
            'domain': 'testuser',
            'counters': {'groups': 5}
        }]

        mock_bot.vk_user.method.return_value = mock_response

        user_info = mock_bot.get_user_info(123)

        assert user_info['id'] == 123
        assert user_info['age'] == datetime.now().year - 1990
        assert user_info['gender'] == 2
        assert user_info['city'] == 1
        assert 'music' in user_info['interests']
        assert 'rock' in user_info['music']
        assert 'sci-fi' in user_info['books']

    def test_search_users(self, mock_bot):
        mock_user_info = {
            'id': 123,
            'age': 30,
            'gender': 2,
            'city': 1,
            'interests': 'music',
            'music': 'rock',
            'books': 'sci-fi',
            'groups': 'group1 group2',
            'domain': 'testuser'
        }

        mock_response = {
            'items': [
                {
                    'id': 456,
                    'first_name': 'Match',
                    'last_name': 'User',
                    'bdate': '01.01.1992',
                    'sex': 1,
                    'city': {'id': 1},
                    'interests': 'music',
                    'is_closed': False,
                    'domain': 'matchuser'
                }
            ]
        }

        mock_bot.vk_user.method.return_value = mock_response
        mock_bot.get_blacklist = MagicMock(return_value=[])

        matches = mock_bot.search_users(mock_user_info)

        assert len(matches) == 1
        assert matches[0]['id'] == 456
        assert matches[0]['first_name'] == 'Match'

    def test_add_to_favorites(self, mock_bot, db_connection):
        mock_bot.db_conn = db_connection
        result = mock_bot.add_to_favorites(123, 456)
        assert result is True

        # Проверяем дублирование
        result = mock_bot.add_to_favorites(123, 456)
        assert result is False

        # Проверяем наличие в БД
        with db_connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM favorites WHERE user_id = 123 AND favorite_id = 456')
            assert cursor.fetchone()[0] == 1

    def test_add_to_blacklist(self, mock_bot, db_connection):
        mock_bot.db_conn = db_connection
        result = mock_bot.add_to_blacklist(123, 789)
        assert result is True

        # Проверяем дублирование
        result = mock_bot.add_to_blacklist(123, 789)
        assert result is False

        # Проверяем наличие в БД
        with db_connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM blacklist WHERE user_id = 123 AND banned_id = 789')
            assert cursor.fetchone()[0] == 1

    def test_toggle_photo_like(self, mock_bot, db_connection):
        mock_bot.db_conn = db_connection
        mock_bot.vk_user.method.return_value = True

        # Первый вызов - ставим лайк
        result = mock_bot.toggle_photo_like(123, 'photo123_456')
        assert result is True

        # Проверяем наличие в БД
        with db_connection.cursor() as cursor:
            cursor.execute(
                "SELECT liked FROM photo_likes WHERE user_id = 123 AND photo_id = 'photo123_456'"
            )
            assert cursor.fetchone()[0] is True

        # Второй вызов - убираем лайк
        result = mock_bot.toggle_photo_like(123, 'photo123_456')
        assert result is False

        # Проверяем обновление в БД
        with db_connection.cursor() as cursor:
            cursor.execute(
                "SELECT liked FROM photo_likes WHERE user_id = 123 AND photo_id = 'photo123_456'"
            )
            assert cursor.fetchone()[0] is False

    def test_show_favorites(self, mock_bot, db_connection):
        mock_bot.db_conn = db_connection

        # Добавляем тестовые данные
        with db_connection.cursor() as cursor:
            cursor.execute(
                'INSERT INTO favorites (user_id, favorite_id, added_at) VALUES (%s, %s, %s)',
                (123, 456, datetime.now())
            )
            db_connection.commit()

        # Мокируем вызов VK API
        mock_user = {
            'first_name': 'Test',
            'last_name': 'Favorite',
            'domain': 'testfav'
        }
        mock_bot.vk_user.method.return_value = [mock_user]

        # Мокируем send_message
        mock_bot.send_message = MagicMock()

        mock_bot.show_favorites(123)

        # Проверяем, что send_message был вызван с ожидаемым текстом
        args, kwargs = mock_bot.send_message.call_args
        assert 'Test Favorite' in kwargs['message']
        assert 'testfav' in kwargs['message']

    def test_show_blacklist(self, mock_bot, db_connection):
        mock_bot.db_conn = db_connection

        # Добавляем тестовые данные
        with db_connection.cursor() as cursor:
            cursor.execute(
                'INSERT INTO blacklist (user_id, banned_id) VALUES (%s, %s)',
                (123, 789)
            )
            db_connection.commit()

        # Мокируем вызов VK API
        mock_user = {
            'first_name': 'Blocked',
            'last_name': 'User',
            'domain': 'blocked'
        }
        mock_bot.vk_user.method.return_value = [mock_user]

        # Мокируем send_message
        mock_bot.send_message = MagicMock()

        mock_bot.show_blacklist(123)

        # Проверяем, что send_message был вызван с ожидаемым текстом
        args, kwargs = mock_bot.send_message.call_args
        assert 'Blocked User' in kwargs['message']
        assert 'blocked' in kwargs['message']

    def test_analyze_interests(self, mock_bot):
        # Тестируем анализ схожести интересов
        text1 = "музыка, книги, программирование"
        text2 = "книги, программирование, спорт"

        similarity = mock_bot.analyze_interests(text1, text2)
        assert 0 < similarity < 1  # Должна быть некоторая схожесть

        # Тест с пустыми строками
        assert mock_bot.analyze_interests("", "something") == 0
        assert mock_bot.analyze_interests("something", "") == 0
        assert mock_bot.analyze_interests("", "") == 0

    def test_get_user_photos(self, mock_bot):
        # Мокируем ответы API
        mock_profile_photos = {
            'items': [
                {'owner_id': 123, 'id': 1, 'likes': {'count': 10}},
                {'owner_id': 123, 'id': 2, 'likes': {'count': 20}}
            ]
        }

        mock_tagged_photos = {
            'items': [
                {'owner_id': 123, 'id': 3, 'likes': {'count': 30}},
                {'owner_id': 123, 'id': 4, 'likes': {'count': 5}}
            ]
        }

        mock_bot.vk_user.method.side_effect = [mock_profile_photos, mock_tagged_photos]

        photos = mock_bot.get_user_photos(123)

        # Должны вернуться 3 самые популярные фотографии
        assert len(photos) == 3
        assert 'photo123_3' in photos  # Самая популярная
        assert 'photo123_2' in photos
        assert 'photo123_1' in photos
        assert 'photo123_4' not in photos  # Менее популярная

    def test_run_handle_message_new(self, mock_bot):
        # Подготовка моков
        mock_event = MagicMock()
        mock_event.type = MagicMock(return_value='message_new')
        mock_event.from_user = True
        mock_event.message = {'from_id': 123, 'text': 'Найти'}

        mock_bot.longpoll.listen = MagicMock(return_value=[mock_event])
        mock_bot.get_user_info = MagicMock(return_value={
            'id': 123, 'age': 30, 'gender': 2, 'city': 1,
            'interests': '', 'music': '', 'books': '', 'groups': '', 'domain': 'test'
        })
        mock_bot.search_users = MagicMock(return_value=[{
            'id': 456, 'first_name': 'Test', 'last_name': 'User',
            'domain': 'testuser', 'bdate': '01.01.1990'
        }])
        mock_bot.show_current_match = MagicMock()

        # Запускаем обработку одного сообщения
        mock_bot.run()

        # Проверяем, что были вызваны нужные методы
        mock_bot.get_user_info.assert_called_once_with(123)
        mock_bot.search_users.assert_called_once()
        mock_bot.show_current_match.assert_called_once_with(123)