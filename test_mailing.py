import os
import sys
import django

# Настраиваем Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memeow_project.settings')
django.setup()

def test_single_user():
    """Тест отправки одному пользователю"""
    from django.contrib.auth.models import User
    from django.core.mail import send_mail
    
    user = User.objects.first()
    if user:
        print(f"Отправка тестового письма {user.email}...")
        
        send_mail(
            'Тест рассылки Memeow',
            f'Привет, {user.username}! Это тестовое письмо.',
            'memeowsubscription@gmail.com',
            [user.email],
            fail_silently=False,
        )
        print("Письмо отправлено!")
    else:
        print("Пользователи не найдены")

def test_daily_digest():
    """Тест ежедневной рассылки"""
    from django.core.management import call_command
    
    print("Запуск тестовой ежедневной рассылки...")
    try:
        call_command('send_meme_digest', 'daily')
        print("Успешно!")
    except Exception as e:
        print(f"Ошибка: {e}")

def test_scheduler():
    """Тест планировщика"""
    from memes.mailing_scheduler import mailing_scheduler
    
    print("Запуск планировщика...")
    mailing_scheduler.start()
    
    print("Статус:", mailing_scheduler.get_status())
    
    # Ждем 10 секунд
    import time
    time.sleep(10)
    
    print("Остановка планировщика...")
    mailing_scheduler.stop()

if __name__ == "__main__":
    print("Выберите тест:")
    print("1. Отправить тестовое письмо")
    print("2. Запустить ежедневную рассылку")
    print("3. Протестировать планировщик")
    
    choice = input("Введите номер (1-3): ")
    
    if choice == "1":
        test_single_user()
    elif choice == "2":
        test_daily_digest()
    elif choice == "3":
        test_scheduler()
    else:
        print("Неверный выбор")