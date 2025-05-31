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


git clone https://github.com/yourusername/vk-dating-bot.git
cd vk-dating-bot
pip install -r requirements.txt
🔧 Настройка
Создайте .env файл:

ini
POSTGRES_DB=dating_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
VK_GROUP_TOKEN=your_token
VK_GROUP_ID=your_group_id
🚀 Запуск
bash
python bot.py
🧪 Тестирование
bash
pytest tests/ -v
pytest --cov=bot --cov-report=term-missing
📊 Структура
vk-dating-bot/
├── bot.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_bot.py
│   └── test_db.py
├── docs/
├── .env
├── requirements.txt
└── README.md
### 📝 Лицензия
MIT License

Python
VK API