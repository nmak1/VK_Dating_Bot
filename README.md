# VK Dating Bot 🤖❤️     

Бот для поиска партнеров ВКонтакте на основе общих интересов, возраста и местоположения.

## 🌟 Особенности    
- 🔍 Поиск по возрасту, полу и городу    
- 🎯 Рекомендации на основе общих интересов      
- 📸 Топ-3 популярных фотографии профиля      
- ⭐ Избранное и черный список      
- 💾 Хранение данных в PostgreSQL     
- 🤖 Полная интеграция с VK API     

## 🛠 Технологии
- Python 3.8+
- VK API
- PostgreSQL
- Scikit-learn
- pytest

## ⚙️ Установка
```bash

git clone https://github.com/nmak1/VK_Dating_Bot
cd VK_Dating_Bot
pip install -r requirements.txt 

🔧 Настройка

Создайте .env файл:

POSTGRES_DB=dating_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
VK_GROUP_TOKEN=your_token
VK_GROUP_ID=12345678
VK_USER_TOKEN=your_user_token  

🚀 Запуск

python bot.py
🧪 Тестирование

pytest tests/ -v
pytest --cov=bot --cov-report=term-missing

📊 Структура
vk_dating_bot/
├── bot.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── constants.py
├── core/
│   ├── __init__.py
│   ├── bot_core.py
│   ├── matching.py
│   ├── vk_api/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── models.py
│   └── db/
│       ├── __init__.py
│       ├── connector.py
│       ├── repositories.py
│       └── models.py
├── handlers/
│   ├── __init__.py
│   ├── message.py
│   └── callback.py
├── services/
│   ├── __init__.py
│   ├── analyzer.py
│   └── formatter.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
├── docs/


📝 Лицензия
MIT License

Python
VK API