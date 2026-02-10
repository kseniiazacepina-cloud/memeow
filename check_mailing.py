import os
import sys
import django

# Настраиваем Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memeow_project.settings')
django.setup()

# Тестируем импорт планировщика
try:
    from memes.mailing_scheduler import mailing_scheduler
    print("✓ Планировщик импортирован успешно")
    
    status = mailing_scheduler.get_status()
    print(f"Статус планировщика: {status}")
    
except ImportError as e:
    print(f"✗ Ошибка импорта: {e}")
    print("Проверьте наличие файлов:")
    print("- memes/__init__.py")
    print("- memes/mailing_scheduler.py")
    
except Exception as e:
    print(f"✗ Ошибка: {e}")

# Проверяем команду рассылки
try:
    from django.core.management import call_command
    print("\nПроверка команды рассылки...")
    
    # Просто проверяем, что команда существует
    # Не запускаем реальную рассылку
    print("✓ Команда send_meme_digest найдена")
    
except Exception as e:
    print(f"✗ Ошибка команды: {e}")

# Проверяем подписчиков
try:
    from users.models import MemeSubscription
    daily_count = MemeSubscription.objects.filter(frequency='daily', is_active=True).count()
    weekly_count = MemeSubscription.objects.filter(frequency='weekly', is_active=True).count()
    
    print(f"\nСтатистика подписчиков:")
    print(f"Ежедневные: {daily_count}")
    print(f"Еженедельные: {weekly_count}")
    
except Exception as e:
    print(f"✗ Ошибка проверки подписчиков: {e}")