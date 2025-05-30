.. VK_Dating_Bot documentation master file, created by└── tests/                  # Тесты
   sphinx-quickstart on Thu May 29 23:56:26 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

VK_Dating_Bot documentation
===========================

Структура проекта
================

::

    VK_Dating_Bot/
    ├── .env                    # Файл конфигурации
    ├── bot.py                  # Основной код бота
    ├── pytest.ini              # Конфигурация тестов
    ├── requirements.txt        # Зависимости
    └── tests/                  # Тесты
        ├── __init__.py
        ├── conftest.py
        ├── test_bot.py
        └── test_db.py
    └── docs/                   # Документация

Конфигурация запуска
--------------------

Для основного бота:
^^^^^^^^^^^^^^^^^^

``Run → Edit Configurations → + → Python``

Параметры:

* **Script path:** ``bot.py``
* **Environment variables:**

  ::

    POSTGRES_DB=dating_bot
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    VK_GROUP_TOKEN=your_token
    VK_GROUP_ID=your_group_id

Для тестов:
^^^^^^^^^^^

``Run → Edit Configurations → + → Python tests → pytest``

Параметры:

* **Target:** "Script path" → указать папку ``tests``
* **Additional arguments:** ``-v --cov=bot --cov-report=term-missing``

.. toctree::
   :maxdepth: 2
   :caption: Contents:

