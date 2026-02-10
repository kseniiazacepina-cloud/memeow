import os
import django
import telebot
from telebot import apihelper
import time
import logging

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memeow_project.settings')
django.setup()

from django.conf import settings
from users.models import TelegramConnection
from django.utils import timezone

# ================== КОНФИГУРАЦИЯ ==================
TOKEN = settings.TELEGRAM_BOT_TOKEN
BOT_USERNAME = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'memeow_subscription_bot')

# ================== ПРОКСИ (если нужно) ==================
# Раскомментируй если Telegram заблокирован:
"""
# Вариант 1: Tor (установи Tor Browser)
# apihelper.proxy = {'https': 'socks5://127.0.0.1:9150'}

# Вариант 2: Публичные прокси (могут не работать):
# apihelper.proxy = {'https': 'http://51.158.68.133:8811'}
# apihelper.proxy = {'https': 'socks5://138.68.161.14:1080'}
"""

# ================== СОЗДАНИЕ БОТА ==================
bot = telebot.TeleBot(TOKEN, parse_mode='Markdown', threaded=False)

# ================== ОБРАБОТЧИКИ ==================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Приветственное сообщение"""
    welcome_text = f"""
👋 *Привет! Я бот для сайта Memeow!*

🤖 *Мои команды:*
/start, /help - это сообщение
/status - статус привязки
/unsubscribe - отписаться от рассылки

🔗 *Как привязать аккаунт:*
1. Зайдите на [сайт Memeow](http://127.0.0.1:8000)
2. В Настройках → Уведомления → "Привязать Telegram"
3. Получите 6-значный код
4. Отправьте его мне

📱 *Username бота:* @{BOT_USERNAME}
🌐 *Сайт:* http://127.0.0.1:8000
    """
    bot.send_message(message.chat.id, welcome_text, disable_web_page_preview=True)


@bot.message_handler(commands=['status'])
def check_status(message):
    """Проверка статуса привязки"""
    try:
        connection = TelegramConnection.objects.get(
            telegram_chat_id=message.chat.id,
            is_verified=True
        )
        
        status_text = f"""
✅ *Аккаунт привязан!*

👤 *Пользователь:* {connection.user.username}
📧 *Email:* {connection.user.email or "не указан"}
🔗 *Telegram:* @{connection.telegram_username or "не указан"}
📅 *Привязан:* {connection.verified_at.strftime('%d.%m.%Y %H:%M')}

🌐 Перейдите на [сайт](http://127.0.0.1:8000/users/settings/) для настройки рассылки.
        """
        bot.send_message(message.chat.id, status_text, disable_web_page_preview=True)
        
    except TelegramConnection.DoesNotExist:
        bot.send_message(message.chat.id,
            "❌ *Telegram не привязан*\n\n"
            "Чтобы привязать:\n"
            "1. Получите код на сайте\n"
            "2. Отправьте его мне"
        )


@bot.message_handler(regexp=r'^\d{6}$')
def verify_code(message):
    """Верификация 6-значного кода"""
    code = message.text.strip()
    logger.info(f"Получен код: {code} от chat_id: {message.chat.id}")
    
    try:
        connection = TelegramConnection.objects.get(
            verification_code=code,
            is_verified=False
        )
        
        # Проверяем, не занят ли chat_id
        existing = TelegramConnection.objects.filter(
            telegram_chat_id=message.chat.id,
            is_verified=True
        ).first()
        
        if existing:
            bot.send_message(
                message.chat.id,
                f"❌ Этот Telegram уже привязан к аккаунту: *{existing.user.username}*\n\n"
                f"Если это ваш аккаунт, войдите на сайт под ним.\n"
                f"Или используйте другой Telegram аккаунт."
            )
            return
        
        # Обновляем привязку
        connection.telegram_chat_id = message.chat.id
        connection.telegram_username = message.from_user.username
        connection.is_verified = True
        connection.verified_at = timezone.now()
        connection.save()
        
        logger.info(f"Аккаунт привязан: {connection.user.username} -> {message.chat.id}")
        
        # Создаем подписку если ее нет
        from users.models import MemeSubscription
        MemeSubscription.objects.get_or_create(
            user=connection.user,
            defaults={
                'channel': 'telegram',
                'frequency': 'weekly',
                'is_active': True
            }
        )
        
        success_text = f"""
✅ *Аккаунт успешно привязан!*

👤 *Пользователь:* {connection.user.username}
📧 *Email:* {connection.user.email or "не указан"}
🔗 *Telegram:* @{message.from_user.username}
📅 *Привязан:* {connection.verified_at.strftime('%d.%m.%Y %H:%M')}

🎉 Теперь вы будете получать лучшие мемы!
Настройте частоту в [настройках](http://127.0.0.1:8000/users/settings/).
        """
        
        bot.send_message(
            message.chat.id,
            success_text,
            disable_web_page_preview=True
        )
        
    except TelegramConnection.DoesNotExist:
        logger.warning(f"Неверный код: {code}")
        bot.send_message(
            message.chat.id,
            "❌ *Неверный код!*\n\n"
            "Код должен быть:\n"
            "• 6 цифр\n"
            "• Действителен 10 минут\n"
            "• Сгенерирован на сайте\n\n"
            "Получите новый код в настройках сайта."
        )
    except Exception as e:
        logger.error(f"Ошибка при верификации: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка. Попробуйте позже.")


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    """Отписка от рассылки"""
    try:
        connection = TelegramConnection.objects.get(
            telegram_chat_id=message.chat.id,
            is_verified=True
        )
        
        # Отключаем подписку
        from users.models import MemeSubscription
        try:
            subscription = connection.user.meme_subscription
            subscription.is_active = False
            subscription.save()
            bot.send_message(
                message.chat.id,
                "✅ Вы отписались от рассылки мемов.\n\n"
                "Чтобы возобновить подписку, зайдите в настройки профиля на сайте."
            )
        except MemeSubscription.DoesNotExist:
            bot.send_message(message.chat.id, "ℹ️ У вас нет активной подписки.")
            
    except TelegramConnection.DoesNotExist:
        bot.send_message(
            message.chat.id,
            "❌ Ваш Telegram не привязан.\n"
            "Сначала привяжите аккаунт через сайт."
        )


@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Обработка всех остальных сообщений"""
    if message.text:
        bot.send_message(
            message.chat.id,
            "🤖 Я понимаю:\n"
            "• 6-значные коды (например: 123456)\n"
            "• Команды: /start, /status, /unsubscribe\n\n"
            "Для привязки получите код на сайте и отправьте мне."
        )


# ================== ЗАПУСК БОТА ==================
def run_bot_with_retry():
    """Запуск бота с повторными попытками"""
    logger.info(f"🚀 Запуск бота @{BOT_USERNAME}")
    
    max_retries = 100  # Много попыток
    retry_count = 0
    retry_delay = 5
    
    while retry_count < max_retries:
        try:
            logger.info(f"Попытка {retry_count + 1}/{max_retries}...")
            
            # Проверяем доступность API
            bot_info = bot.get_me()
            logger.info(f"✅ Бот запущен: @{bot_info.username} ({bot_info.first_name})")
            logger.info(f"🆔 ID бота: {bot_info.id}")
            
            # Запускаем polling с увеличенными таймаутами
            bot.polling(
                none_stop=True,      # Не останавливаться при ошибках
                interval=3,          # Интервал между запросами
                timeout=30,          # Таймаут запроса
                long_polling_timeout=30
            )
            
        except telebot.apihelper.ApiTelegramException as e:
            if "Conflict" in str(e):
                logger.error("❌ Другой экземпляр бота уже запущен!")
                break
            elif "Forbidden" in str(e):
                logger.error("❌ Бот заблокирован пользователем")
                break
            else:
                logger.warning(f"⚠️ Ошибка Telegram API: {e}")
                
        except requests.exceptions.ReadTimeout:
            logger.warning(f"⏱️ Таймаут чтения. Повтор через {retry_delay} сек...")
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"🔌 Ошибка подключения: {e}")
            logger.warning(f"Проверьте интернет. Повтор через {retry_delay} сек...")
            
        except Exception as e:
            logger.error(f"⚠️ Неизвестная ошибка: {type(e).__name__}: {e}")
            
        # Задержка перед повторной попыткой
        retry_count += 1
        logger.info(f"⏳ Повторная попытка через {retry_delay} сек...")
        time.sleep(retry_delay)
        
        # Увеличиваем задержку с каждой попыткой (exponential backoff)
        retry_delay = min(retry_delay * 1.5, 60)  # Макс 60 секунд
    
    logger.error(f"❌ Бот остановлен после {max_retries} попыток")


if __name__ == '__main__':
    import requests
    
    print("=" * 50)
    print(f"🤖 Memeow Telegram Bot")
    print(f"📱 Username: @{BOT_USERNAME}")
    print(f"🔑 Token: {TOKEN[:15]}...")
    print("=" * 50)
    
    # Проверяем токен перед запуском
    try:
        test_url = f'https://api.telegram.org/bot{TOKEN}/getMe'
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200 and response.json().get('ok'):
            print("✅ Токен проверен успешно")
            run_bot_with_retry()
        else:
            print(f"❌ Ошибка токена: {response.json()}")
            
    except Exception as e:
        print(f"❌ Не могу проверить токен: {e}")
        print("Проверьте интернет-соединение и настройки прокси")