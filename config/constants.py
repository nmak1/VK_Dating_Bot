class VkConstants:
    API_VERSION = "5.131"
    MAX_SEARCH_RESULTS = 1000
    USER_FIELDS = "bdate,sex,city,interests,music,books,groups,domain,counters"
    PHOTO_SIZES = ["photo_50", "photo_100", "photo_200"]
    SEARCH_DELAY = 0.34

class DbConstants:
    TABLES = {
        'favorites': "favorites",
        'blacklist': "blacklist",
        'photo_likes': "photo_likes"
    }
    MAX_RETRIES = 3

class BotConstants:
    AGE_RANGE = 5
    MIN_AGE = 18
    MAX_AGE = 100
    MAX_PHOTOS = 3
    WEIGHTS = {
        'age': 0.3,
        'city': 0.2,
        'interests': 0.2,
        'music': 0.1,
        'books': 0.1,
        'groups': 0.1
    }

class Messages:
    WELCOME = "Привет! Я бот для знакомств. Нажми 'Найти' чтобы начать."
    NO_MATCHES = "Не найдено подходящих пользователей."
    FAVORITE_ADDED = "Добавлено в избранное!"
    PROFILE_TEMPLATE = """{name}
Возраст: {age}
Город: {city}
Ссылка: {link}"""