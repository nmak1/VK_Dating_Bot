import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
import json
from datetime import datetime


class VKDatingBot:
    def __init__(self, group_token, user_token, group_id):
        self.vk_group = vk_api.VkApi(token=group_token)
        self.vk_user = vk_api.VkApi(token=user_token)
        self.longpoll = VkBotLongPoll(self.vk_group, group_id)
        self.keyboard = None
        self.create_keyboard()
        self.current_user_index = 0
        self.current_matches = []
        self.favorites = self.load_favorites()

    def create_keyboard(self):
        """Создает интерактивную клавиатуру с кнопками"""
        self.keyboard = VkKeyboard(one_time=False)
        self.keyboard.add_button('Найти', color=VkKeyboardColor.POSITIVE)
        self.keyboard.add_button('Следующий', color=VkKeyboardColor.PRIMARY)
        self.keyboard.add_line()
        self.keyboard.add_button('В избранное', color=VkKeyboardColor.SECONDARY)
        self.keyboard.add_button('Избранные', color=VkKeyboardColor.SECONDARY)

    def load_favorites(self):
        """Загружает избранное из файла"""
        try:
            with open('favorites.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_favorites(self):
        """Сохраняет избранное в файл"""
        with open('favorites.json', 'w') as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)

    def get_user_info(self, user_id):
        """Получает возраст, пол и город пользователя"""
        response = self.vk_user.method('users.get', {
            'user_ids': user_id,
            'fields': 'bdate,sex,city'
        })

        if not response:
            return None

        user = response[0]
        age = None
        city = None

        # Вычисляем возраст из даты рождения
        if 'bdate' in user:
            bdate = user['bdate'].split('.')
            if len(bdate) == 3:
                birth_year = int(bdate[2])
                current_year = datetime.now().year
                age = current_year - birth_year

        # Получаем ID города
        if 'city' in user:
            city = user['city']['id']

        return {
            'age': age,
            'gender': user.get('sex'),
            'city': city
        }

    def search_users(self, age, gender, city):
        """Ищет потенциальные пары"""
        # Противоположный пол
        search_gender = 1 if gender == 2 else 2

        response = self.vk_user.method('users.search', {
            'age_from': age - 3,
            'age_to': age + 3,
            'sex': search_gender,
            'city': city,
            'has_photo': 1,
            'count': 100,
            'fields': 'domain',
            'status': 6  # "не женат/не замужем"
        })

        return response.get('items', [])

    def get_top_photos(self, user_id):
        """Получает топ-3 фотографии по количеству лайков"""
        response = self.vk_user.method('photos.get', {
            'owner_id': user_id,
            'album_id': 'profile',
            'extended': 1
        })

        if not response or 'items' not in response:
            return []

        # Сортируем фотографии по лайкам и берем топ-3
        photos = sorted(
            response['items'],
            key=lambda x: x['likes']['count'],
            reverse=True
        )[:3]

        # Получаем ID фотографий в формате 'owner_id_photo_id'
        return [f"photo{photo['owner_id']}_{photo['id']}" for photo in photos]

    def send_message(self, user_id, message, attachments=None):
        """Отправляет сообщение пользователю"""
        self.vk_group.method('messages.send', {
            'user_id': user_id,
            'message': message,
            'random_id': get_random_id(),
            'keyboard': self.keyboard.get_keyboard(),
            'attachment': ','.join(attachments) if attachments else None
        })

    def show_match(self, user_id, match_index):
        """Показывает информацию о найденной паре"""
        if match_index >= len(self.current_matches):
            self.send_message(user_id, "Больше подходящих пользователей не найдено.")
            return

        match = self.current_matches[match_index]
        profile_link = f"https://vk.com/{match['domain']}"

        # Получаем топ фотографии
        photos = self.get_top_photos(match['id'])

        # Формируем сообщение
        message = (
            f"{match['first_name']} {match['last_name']}\n"
            f"Ссылка: {profile_link}"
        )

        self.send_message(user_id, message, photos)

    def add_to_favorites(self, user_id, match_index):
        """Добавляет текущую пару в избранное"""
        if match_index >= len(self.current_matches):
            return

        match = self.current_matches[match_index]

        # Проверяем, нет ли уже в избранном
        if not any(fav['id'] == match['id'] for fav in self.favorites):
            # Получаем фотографии для записи в избранное
            photos = self.get_top_photos(match['id'])

            self.favorites.append({
                'id': match['id'],
                'first_name': match['first_name'],
                'last_name': match['last_name'],
                'domain': match['domain'],
                'photos': photos,
                'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            self.save_favorites()
            self.send_message(user_id, "Добавлено в избранное!")
        else:
            self.send_message(user_id, "Уже в избранном!")

    def show_favorites(self, user_id):
        """Показывает список избранных"""
        if not self.favorites:
            self.send_message(user_id, "В избранном пока никого нет.")
            return

        message = "Ваши избранные:\n\n"
        for i, fav in enumerate(self.favorites, 1):
            message += (
                f"{i}. {fav['first_name']} {fav['last_name']}\n"
                f"Добавлен: {fav['added_at']}\n"
                f"Ссылка: https://vk.com/{fav['domain']}\n\n"
            )

        self.send_message(user_id, message.strip())

    def run(self):
        """Основной цикл бота"""
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                user_id = event.message['from_id']
                text = event.message['text'].lower()

                if text == 'начать' or text == 'привет':
                    self.send_message(
                        user_id,
                        "Привет! Я бот для знакомств. Нажми 'Найти', чтобы начать поиск."
                    )

                elif text == 'найти':
                    # Получаем информацию о пользователе
                    user_info = self.get_user_info(user_id)

                    if not user_info or not all(user_info.values()):
                        self.send_message(
                            user_id,
                            "Не удалось получить вашу информацию (возраст, пол, город). "
                            "Пожалуйста, заполните эти данные в вашем профиле ВК."
                        )
                        continue

                    # Ищем пары
                    self.current_matches = self.search_users(
                        user_info['age'],
                        user_info['gender'],
                        user_info['city']
                    )

                    if not self.current_matches:
                        self.send_message(user_id, "Не найдено подходящих пользователей.")
                        continue

                    self.current_user_index = 0
                    self.show_match(user_id, self.current_user_index)

                elif text == 'следующий':
                    if not self.current_matches:
                        self.send_message(user_id, "Сначала нажмите 'Найти'.")
                        continue

                    self.current_user_index += 1
                    self.show_match(user_id, self.current_user_index)

                elif text == 'в избранное':
                    if not self.current_matches:
                        self.send_message(user_id, "Сначала нажмите 'Найти'.")
                        continue

                    self.add_to_favorites(user_id, self.current_user_index)

                elif text == 'избранные':
                    self.show_favorites(user_id)

                else:
                    self.send_message(
                        user_id,
                        "Используйте кнопки для взаимодействия с ботом."
                    )


if __name__ == '__main__':
    # Замените эти значения на свои реальные токены и ID группы
    GROUP_TOKEN = 'ваш_токен_группы'
    USER_TOKEN = 'ваш_пользовательский_токен'
    GROUP_ID = 12345678  # ваш ID группы

    bot = VKDatingBot(GROUP_TOKEN, USER_TOKEN, GROUP_ID)
    bot.run()