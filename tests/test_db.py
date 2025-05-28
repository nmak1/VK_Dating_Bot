from datetime import datetime


class TestDatabaseOperations:
    def test_favorites_operations(self, db_connection):
        # Тестируем операции с избранным
        with db_connection.cursor() as cursor:
            # Добавляем запись
            cursor.execute(
                'INSERT INTO favorites (user_id, favorite_id, added_at) VALUES (%s, %s, %s)',
                (123, 456, datetime.now())
            )
            db_connection.commit()

            # Проверяем наличие
            cursor.execute('SELECT COUNT(*) FROM favorites WHERE user_id = 123 AND favorite_id = 456')
            assert cursor.fetchone()[0] == 1

            # Пробуем добавить дубликат
            cursor.execute(
                'INSERT INTO favorites (user_id, favorite_id, added_at) VALUES (%s, %s, %s) '
                'ON CONFLICT (user_id, favorite_id) DO NOTHING',
                (123, 456, datetime.now())
            )
            db_connection.commit()

            # Должна остаться одна запись
            cursor.execute('SELECT COUNT(*) FROM favorites WHERE user_id = 123')
            assert cursor.fetchone()[0] == 1

    def test_blacklist_operations(self, db_connection):
        # Тестируем операции с черным списком
        with db_connection.cursor() as cursor:
            # Добавляем запись
            cursor.execute(
                'INSERT INTO blacklist (user_id, banned_id) VALUES (%s, %s)',
                (123, 789)
            )
            db_connection.commit()

            # Проверяем наличие
            cursor.execute('SELECT COUNT(*) FROM blacklist WHERE user_id = 123 AND banned_id = 789')
            assert cursor.fetchone()[0] == 1

            # Пробуем добавить дубликат
            cursor.execute(
                'INSERT INTO blacklist (user_id, banned_id) VALUES (%s, %s) '
                'ON CONFLICT (user_id, banned_id) DO NOTHING',
                (123, 789)
            )
            db_connection.commit()

            # Должна остаться одна запись
            cursor.execute('SELECT COUNT(*) FROM blacklist WHERE user_id = 123')
            assert cursor.fetchone()[0] == 1

    def test_photo_likes_operations(self, db_connection):
        # Тестируем операции с лайками фотографий
        with db_connection.cursor() as cursor:
            # Добавляем запись
            cursor.execute(
                'INSERT INTO photo_likes (user_id, photo_id, liked) VALUES (%s, %s, %s)',
                (123, 'photo123_456', True)
            )
            db_connection.commit()

            # Проверяем наличие
            cursor.execute(
                " SELECT liked FROM photo_likes WHERE user_id = 123 AND photo_id = 'photo123_456' ")
            assert cursor.fetchone()[0] is True

            # Обновляем запись
            cursor.execute(
                'UPDATE photo_likes SET liked = %s WHERE user_id = %s AND photo_id = %s',
                (False, 123, 'photo123_456')
            )
            db_connection.commit()

            # Проверяем обновление
            cursor.execute(
                "SELECT liked FROM photo_likes WHERE user_id = 123 AND photo_id = 'photo123_456' ")
            assert cursor.fetchone()[0] is False