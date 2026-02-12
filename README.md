# Memeow 🐱

Memeow - это веб-платформа для публикации и обмена мемами. Пользователи могут загружать свои мемы, ставить лайки, добавлять в избранное и просматривать мемы по тегам.

---

# 🚀 Быстрый старт

# 1. Клонирование репозитория
```bash
git clone https://github.com/kseniiazacepina-cloud/memeow.git
cd memeow
```

# 2. Создание виртуального окружения
Windows:
```bash
python -m venv venv
venv\Scripts\activate
```
Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

# 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

# 4. Настройка базы данных
```bash
python manage.py migrate
```

# 5. Запуск сервера
```bash
python manage.py runserver
```

# Откройте в браузере:
http://127.0.0.1:8000/
