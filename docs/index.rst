.. VK_Dating_Bot documentation master file, created by
   sphinx-quickstart on Thu May 29 23:56:26 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

VK_Dating_Bot documentation
===========================

Структура проекта
================

::

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

