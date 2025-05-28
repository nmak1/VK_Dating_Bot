import os
import random
import string
from datetime import datetime

import psycopg2
import vk_api
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

# Загрузка переменных окружения
load_dotenv()


class VKAdvancedDatingBot:
    def __init__(self, group_token, group_id):
        self.vk_group = vk_api.VkApi(token=group_token)
        self.vk_user = None  # Будет установлен после получения токена от пользователя
        self.longpoll = VkBotLongPoll(self.vk_group, group_id)
        self.keyboard = None
        self.create_keyboards()
        self.current_user_index = 0
        self.current_matches = []
        self.user_states = {}  # Хранение состояний пользователей
        self.db_conn = self.init_db()
        self.weights = {
            'age': 0.3,
            'city': 0.2,
            'interests': 0.2,
            'music': 0.1,
            'books': 0.1,
            'groups': 0.1
        }

    def init_db(self):
        """Инициализация подключения к PostgreSQL"""
        try:
            conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB', 'dating_bot'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432')
            )

            # Создание таблиц, если они не существуют
            with conn.cursor() as cursor:
                # Таблица избранных
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS favorites (
                        user_id BIGINT,
                        favorite_id BIGINT,
                        added_at TIMESTAMP,
                        PRIMARY KEY (user_id, favorite_id)
                ''')

                # Таблица черного списка
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blacklist (
                        user_id BIGINT,
                        banned_id BIGINT,
                        PRIMARY KEY (user_id, banned_id)
                ''')

                # Таблица лайков фотографий
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS photo_likes (
                        user_id BIGINT,
                        photo_id TEXT,
                        liked BOOLEAN,
                        PRIMARY KEY (user_id, photo_id)
                ''')

                conn.commit()

            return conn
        except Exception as e:
            print(f"Ошибка подключения к PostgreSQL: {e}")
            raise

    def create_keyboards(self):
        """Создает различные клавиатуры для взаимодействия"""
        # Основная клавиатура
        self.main_keyboard = VkKeyboard(one_time=False)
        self.main_keyboard.add_button('Найти', color=VkKeyboardColor.POSITIVE)
        self.main_keyboard.add_button('Следующий', color=VkKeyboardColor.PRIMARY)
        self.main_keyboard.add_line()
        self.main_keyboard.add_button('В избранное', color=VkKeyboardColor.SECONDARY)
        self.main_keyboard.add_button('Избранные', color=VkKeyboardColor.SECONDARY)
        self.main_keyboard.add_line()
        self.main_keyboard.add_button('Черный список', color=VkKeyboardColor.NEGATIVE)

        # Клавиатура для фотографий
        self.photo_keyboard = VkKeyboard(one_time=False)
        for i in range(1, 4):
            self.photo_keyboard.add_button(f'❤️ Фото {i}', color=VkKeyboardColor.SECONDARY)
            if i < 3:
                self.photo_keyboard.add_line()

        # Клавиатура для подтверждения
        self.confirm_keyboard = VkKeyboard(one_time=True)
        self.confirm_keyboard.add_button('Да', color=VkKeyboardColor.POSITIVE)
        self.confirm_keyboard.add_button('Нет', color=VkKeyboardColor.NEGATIVE)

    def get_user_token(self, user_id):
        """Запрашивает токен пользователя"""
        self.send_message(user_id,
                          "Для работы бота нужен ваш токен доступа VK. "
                          "Вы можете получить его здесь: https://vkhost.github.io/. "
                          "Отправьте его мне сообщением. "
                          "Бот не сохраняет ваш токен и использует его только для текущей сессии.")

        # Устанавливаем состояние ожидания токена
        self.user_states[user_id] = 'waiting_for_token'

    def analyze_interests(self, text1, text2):
        """Анализирует сходство интересов с помощью TF-IDF и косинусного сходства"""
        if not text1 or not text2:
            return 0

        # Очистка текста
        translator = str.maketrans('', '', string.punctuation)
        text1 = text1.lower().translate(translator)
        text2 = text2.lower().translate(translator)

        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return 0

    def get_user_info(self, user_id):
        """Получает расширенную информацию о пользователе"""
        response = self.vk_user.method('users.get', {
            'user_ids': user_id,
            'fields': 'bdate,sex,city,interests,music,books,groups,domain,counters'
        })

        if not response:
            return None

        user = response[0]
        age = None
        city = None

        # Вычисляем возраст
        if 'bdate' in user:
            bdate = user['bdate'].split('.')
            if len(bdate) == 3:
                birth_year = int(bdate[2])
                current_year = datetime.now().year
                age = current_year - birth_year

        # Получаем информацию о городе
        city_id = user.get('city', {}).get('id') if 'city' in user else None

        # Получаем список групп пользователя
        groups = []
        if 'groups' in user and user['counters'].get('groups', 0) > 0:
            groups_response = self.vk_user.method('groups.get', {
                'user_id': user_id,
                'extended': 1,
                'fields': 'activity',
                'count': 100
            })
            groups = [g['name'] for g in groups_response.get('items', [])]

        return {
            'id': user['id'],
            'age': age,
            'gender': user.get('sex'),
            'city': city_id,
            'interests': user.get('interests', ''),
            'music': user.get('music', ''),
            'books': user.get('books', ''),
            'groups': ' '.join(groups),
            'domain': user.get('domain', 'id' + str(user['id']))
        }

    def search_users(self, user_info):
        """Расширенный поиск пользователей с учетом интересов и обходом ограничений"""
        search_gender = 1 if user_info['gender'] == 2 else 2
        all_matches = []

        # Поиск по разным критериям для обхода ограничения в 1000 результатов
        search_params = [
            {'has_photo': 1, 'status': 6},  # Не женат/не замужем
            {'has_photo': 1, 'status': 1},  # Не указано
            {'has_photo': 1}  # Без фильтра по статусу
        ]

        for params in search_params:
            params.update({
                'age_from': user_info['age'] - 5,
                'age_to': user_info['age'] + 5,
                'sex': search_gender,
                'city': user_info['city'],
                'count': 200,
                'fields': 'interests,music,books,groups,domain,counters',
                'offset': random.randint(0, 800)  # Случайное смещение для разнообразия
            })

            response = self.vk_user.method('users.search', params)
            all_matches.extend(response.get('items', []))

        # Удаляем дубликаты
        unique_matches = {m['id']: m for m in all_matches}.values()

        # Фильтруем черный список
        blacklist = self.get_blacklist(user_info['id'])

        filtered_matches = [
            m for m in unique_matches
            if m['id'] not in blacklist and
               not m.get('is_closed', True) and
               'city' in m and
               m.get('city', {}).get('id') == user_info['city']
        ]

        # Сортируем по релевантности
        scored_matches = []
        for match in filtered_matches:
            score = 0

            # Совпадение по возрасту
            if 'bdate' in match:
                bdate = match['bdate'].split('.')
                if len(bdate) == 3:
                    age = datetime.now().year - int(bdate[2])
                    age_diff = abs(age - user_info['age'])
                    score += self.weights['age'] * (1 - min(age_diff / 10, 1))

            # Совпадение по городу
            if 'city' in match and match['city']['id'] == user_info['city']:
                score += self.weights['city']

            # Анализ интересов
            interests_sim = self.analyze_interests(
                user_info['interests'],
                match.get('interests', ''))
            score += self.weights['interests'] * interests_sim

            # Анализ музыкальных предпочтений
            music_sim = self.analyze_interests(
                user_info['music'],
                match.get('music', ''))
            score += self.weights['music'] * music_sim

            # Анализ книг
            books_sim = self.analyze_interests(
                user_info['books'],
                match.get('books', ''))
            score += self.weights['books'] * books_sim

            # Анализ групп (если есть доступ)
            if 'groups' in match and user_info['groups']:
                groups_sim = self.analyze_interests(
                    user_info['groups'],
                    ' '.join([g['name'] for g in match.get('groups', [])]))
                score += self.weights['groups'] * groups_sim

            scored_matches.append((score, match))

        # Сортируем по убыванию рейтинга
        scored_matches.sort(reverse=True, key=lambda x: x[0])

        return [m[1] for m in scored_matches[:100]]  # Возвращаем топ-100

    def get_user_photos(self, user_id):
        """Получает фотографии пользователя: аватарки и фотографии с отметками"""
        photos = []

        # Получаем фотографии профиля
        try:
            profile_photos = self.vk_user.method('photos.get', {
                'owner_id': user_id,
                'album_id': 'profile',
                'extended': 1,
                'count': 50
            })
            photos.extend(profile_photos.get('items', []))
        except:
            pass

        # Получаем фотографии с отметками
        try:
            tagged_photos = self.vk_user.method('photos.getUserPhotos', {
                'user_id': user_id,
                'extended': 1,
                'count': 50
            })
            photos.extend(tagged_photos.get('items', []))
        except:
            pass

        # Сортируем все фотографии по лайкам и выбираем топ-3
        top_photos = sorted(
            photos,
            key=lambda x: x['likes']['count'],
            reverse=True
        )[:3]

        return [f"photo{photo['owner_id']}_{photo['id']}" for photo in top_photos]

    def send_message(self, user_id, message, attachments=None, keyboard=None):
        """Отправляет сообщение с возможными вложениями и клавиатурой"""
        self.vk_group.method('messages.send', {
            'user_id': user_id,
            'message': message,
            'random_id': get_random_id(),
            'keyboard': keyboard.get_keyboard() if keyboard else self.main_keyboard.get_keyboard(),
            'attachment': ','.join(attachments) if attachments else None
        })

    def toggle_photo_like(self, user_id, photo_id):
        """Ставит/убирает лайк на фотографии"""
        owner_id, photo_id = photo_id.split('_')[0][5:], photo_id.split('_')[1]
        full_photo_id = f"photo{owner_id}_{photo_id}"

        try:
            with self.db_conn.cursor() as cursor:
                # Проверяем текущее состояние лайка
                cursor.execute('''
                    SELECT liked FROM photo_likes 
                    WHERE user_id = %s AND photo_id = %s
                    FOR UPDATE
                ''', (user_id, full_photo_id))

                result = cursor.fetchone()

                if result:
                    liked = not result[0]
                    cursor.execute('''
                        UPDATE photo_likes SET liked = %s 
                        WHERE user_id = %s AND photo_id = %s
                    ''', (liked, user_id, full_photo_id))
                else:
                    liked = True
                    cursor.execute('''
                        INSERT INTO photo_likes (user_id, photo_id, liked) 
                        VALUES (%s, %s, %s)
                    ''', (user_id, full_photo_id, True))

                self.db_conn.commit()

                # Отправляем API-запрос на установку/снятие лайка
                try:
                    if liked:
                        self.vk_user.method('likes.add', {
                            'type': 'photo',
                            'owner_id': owner_id,
                            'item_id': photo_id
                        })
                    else:
                        self.vk_user.method('likes.delete', {
                            'type': 'photo',
                            'owner_id': owner_id,
                            'item_id': photo_id
                        })
                except Exception as e:
                    print(f"Error toggling like: {e}")

                return liked
        except Exception as e:
            print(f"Ошибка при переключении лайка: {e}")
            self.db_conn.rollback()
            return False

    def add_to_favorites(self, user_id, favorite_id):
        """Добавляет пользователя в избранное"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO favorites (user_id, favorite_id, added_at) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, favorite_id) DO NOTHING
                    RETURNING user_id
                ''', (user_id, favorite_id, datetime.now()))

                self.db_conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при добавлении в избранное: {e}")
            self.db_conn.rollback()
            return False

    def add_to_blacklist(self, user_id, banned_id):
        """Добавляет пользователя в черный список"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO blacklist (user_id, banned_id) 
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, banned_id) DO NOTHING
                    RETURNING user_id
                ''', (user_id, banned_id))

                self.db_conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при добавлении в черный список: {e}")
            self.db_conn.rollback()
            return False

    def show_favorites(self, user_id):
        """Показывает список избранных"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute('''
                    SELECT favorite_id, added_at FROM favorites 
                    WHERE user_id = %s 
                    ORDER BY added_at DESC
                ''', (user_id,))

                favorites = cursor.fetchall()

                if not favorites:
                    self.send_message(user_id, "В избранном пока никого нет.")
                    return

                message = "Ваши избранные:\n\n"
                for i, (favorite_id, added_at) in enumerate(favorites, 1):
                    user_info = self.vk_user.method('users.get', {
                        'user_ids': favorite_id,
                        'fields': 'domain'
                    })[0]

                    message += (
                        f"{i}. {user_info['first_name']} {user_info['last_name']}\n"
                        f"Добавлен: {added_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Ссылка: https://vk.com/{user_info.get('domain', 'id' + str(favorite_id))}\n\n"
                    )

                self.send_message(user_id, message.strip())
        except Exception as e:
            print(f"Ошибка при получении избранного: {e}")
            self.send_message(user_id, "Произошла ошибка при получении избранного.")

    def show_blacklist(self, user_id):
        """Показывает черный список"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute('''
                    SELECT banned_id FROM blacklist 
                    WHERE user_id = %s 
                    ORDER BY banned_id DESC
                ''', (user_id,))

                blacklist = cursor.fetchall()

                if not blacklist:
                    self.send_message(user_id, "Черный список пуст.")
                    return

                message = "Ваш черный список:\n\n"
                for i, (banned_id,) in enumerate(blacklist, 1):
                    user_info = self.vk_user.method('users.get', {
                        'user_ids': banned_id,
                        'fields': 'domain'
                    })[0]

                    message += (
                        f"{i}. {user_info['first_name']} {user_info['last_name']}\n"
                        f"Ссылка: https://vk.com/{user_info.get('domain', 'id' + str(banned_id))}\n\n"
                    )

                self.send_message(user_id, message.strip())
        except Exception as e:
            print(f"Ошибка при получении черного списка: {e}")
            self.send_message(user_id, "Произошла ошибка при получении черного списка.")

    def get_blacklist(self, user_id):
        """Получает черный список пользователя"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute('''
                    SELECT banned_id FROM blacklist 
                    WHERE user_id = %s
                ''', (user_id,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка при получении черного списка: {e}")
            return []

    def show_current_match(self, user_id):
        """Показывает текущую подобранную пару"""
        if self.current_user_index >= len(self.current_matches):
            self.send_message(user_id, "Больше подходящих пользователей не найдено.")
            return

        match = self.current_matches[self.current_user_index]
        profile_link = f"https://vk.com/{match.get('domain', 'id' + str(match['id']))}"

        # Получаем фотографии
        photos = self.get_user_photos(match['id'])

        # Формируем сообщение
        message = (
            f"{match['first_name']} {match['last_name']}\n"
            f"Ссылка: {profile_link}\n\n"
        )

        # Добавляем информацию о возрасте, если есть
        if 'bdate' in match:
            bdate = match['bdate'].split('.')
            if len(bdate) == 3:
                age = datetime.now().year - int(bdate[2])
                message += f"Возраст: {age}\n"

        # Добавляем интересы, если есть
        if match.get('interests'):
            message += f"Интересы: {match['interests'][:100]}...\n"

        self.send_message(
            user_id,
            message.strip(),
            attachments=photos,
            keyboard=self.photo_keyboard
        )

    def run(self):
        """Основной цикл бота"""
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                user_id = event.message['from_id']
                text = event.message['text'].lower()

                # Обработка состояния ожидания токена
                if self.user_states.get(user_id) == 'waiting_for_token':
                    try:
                        # Проверяем токен
                        test_vk = vk_api.VkApi(token=text)
                        test_vk.method('users.get', {})

                        # Токен валиден, сохраняем
                        self.vk_user = vk_api.VkApi(token=text)
                        self.user_states[user_id] = None
                        self.send_message(
                            user_id,
                            "Токен успешно принят! Теперь вы можете использовать все функции бота.",
                            keyboard=self.main_keyboard
                        )
                    except:
                        self.send_message(
                            user_id,
                            "Неверный токен. Пожалуйста, попробуйте еще раз или проверьте разрешения."
                        )
                    continue

                # Если токен пользователя не установлен
                if not self.vk_user:
                    self.get_user_token(user_id)
                    continue

                # Основные команды
                if text == 'начать' or text == 'привет':
                    self.send_message(
                        user_id,
                        "Привет! Я продвинутый бот для знакомств. "
                        "Нажми 'Найти', чтобы начать поиск.",
                        keyboard=self.main_keyboard
                    )

                elif text == 'найти':
                    # Получаем информацию о пользователе
                    user_info = self.get_user_info(user_id)

                    if not user_info or not all([user_info['age'], user_info['gender'], user_info['city']]):
                        self.send_message(
                            user_id,
                            "Не удалось получить вашу информацию (возраст, пол, город). "
                            "Пожалуйста, заполните эти данные в вашем профиле ВК."
                        )
                        continue

                    # Ищем пары
                    self.current_matches = self.search_users(user_info)

                    if not self.current_matches:
                        self.send_message(user_id, "Не найдено подходящих пользователей.")
                        continue

                    self.current_user_index = 0
                    self.show_current_match(user_id)

                elif text == 'следующий':
                    if not self.current_matches:
                        self.send_message(user_id, "Сначала нажмите 'Найти'.")
                        continue

                    self.current_user_index += 1
                    if self.current_user_index >= len(self.current_matches):
                        self.current_user_index = 0

                    self.show_current_match(user_id)

                elif text == 'в избранное':
                    if not self.current_matches:
                        self.send_message(user_id, "Сначала нажмите 'Найти'.")
                        continue

                    match = self.current_matches[self.current_user_index]
                    if self.add_to_favorites(user_id, match['id']):
                        self.send_message(user_id, "Добавлено в избранное!")
                    else:
                        self.send_message(user_id, "Уже в избранном!")

                elif text == 'избранные':
                    self.show_favorites(user_id)

                elif text == 'черный список':
                    self.show_blacklist(user_id)
                    self.send_message(
                        user_id,
                        "Хотите добавить текущего пользователя в черный список?",
                        keyboard=self.confirm_keyboard
                    )
                    self.user_states[user_id] = 'waiting_blacklist_confirm'

                elif text == 'да' and self.user_states.get(user_id) == 'waiting_blacklist_confirm':
                    if not self.current_matches:
                        self.send_message(user_id, "Ошибка: нет текущего пользователя.")
                        self.user_states[user_id] = None
                        continue

                    match = self.current_matches[self.current_user_index]
                    if self.add_to_blacklist(user_id, match['id']):
                        self.send_message(user_id, "Пользователь добавлен в черный список.")
                    else:
                        self.send_message(user_id, "Пользователь уже в черном списке.")

                    self.user_states[user_id] = None

                elif text == 'нет' and self.user_states.get(user_id) == 'waiting_blacklist_confirm':
                    self.send_message(user_id, "Хорошо, пользователь не будет добавлен в черный список.")
                    self.user_states[user_id] = None

                elif text.startswith('❤️ фото'):
                    if not self.current_matches:
                        self.send_message(user_id, "Сначала нажмите 'Найти'.")
                        continue

                    try:
                        photo_num = int(text.split()[-1]) - 1
                        match = self.current_matches[self.current_user_index]
                        photos = self.get_user_photos(match['id'])

                        if 0 <= photo_num < len(photos):
                            liked = self.toggle_photo_like(user_id, photos[photo_num])
                            status = "поставлен" if liked else "удален"
                            self.send_message(
                                user_id,
                                f"Лайк {status} на фото {photo_num + 1}.",
                                keyboard=self.photo_keyboard
                            )
                        else:
                            self.send_message(user_id, "Неверный номер фото.")
                    except:
                        self.send_message(user_id, "Ошибка обработки команды.")

                else:
                    self.send_message(
                        user_id,
                        "Используйте кнопки для взаимодействия с ботом."
                    )

    def __del__(self):
        """Закрываем соединение с БД при уничтожении объекта"""
        if hasattr(self, 'db_conn') and self.db_conn:
            self.db_conn.close()


if __name__ == '__main__':
    # Замените эти значения на свои реальные токены и ID группы
    GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN', 'ваш_токен_группы')
    GROUP_ID = int(os.getenv('VK_GROUP_ID', '12345678'))  # ваш ID группы

    bot = VKAdvancedDatingBot(GROUP_TOKEN, GROUP_ID)
    try:
        bot.run()
    except KeyboardInterrupt:
        print("Бот остановлен")
    finally:
        # Гарантированное закрытие соединения с БД при завершении
        if hasattr(bot, 'db_conn') and bot.db_conn:
            bot.db_conn.close()