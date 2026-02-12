Memeow - это веб-платформа для создания, публикации и обмена мемами. Пользователи могут загружать свои мемы, ставить лайки, добавлять в избранное и просматривать мемы по тегам.

https://static/images/logo.png

🚀 Быстрый старт
1. Клонирование репозитория
# Клонируйте репозиторий
git clone https://github.com/kseniiazacepina-cloud/memeow.git
cd memeow

2. Создание виртуального окружения
# Для Windows
python -m venv venv
venv\Scripts\activate

# Для Linux/Mac
python3 -m venv venv
source venv/bin/activate

3. Установка зависимостей
pip install -r requirements.txt

4. Настройка базы данных
# Применение миграций
python manage.py migrate

# Создание суперпользователя (админа)
python manage.py createsuperuser
# Следуйте инструкциям для создания админа

5. Запуск сервера разработки
python manage.py runserver
Теперь откройте браузер и перейдите по адресу:

🌐 Сайт: http://127.0.0.1:8000/