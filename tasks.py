from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from memes.models import Meme
from datetime import datetime, timedelta
import random

def send_daily_digest():
    """Отправка ежедневного дайджеста подписчикам"""
    # Получаем всех пользователей с подпиской
    subscribers = User.objects.filter(profile__email_subscription=True)
    
    # Выбираем 5 случайных мемов за последнюю неделю
    week_ago = datetime.now() - timedelta(days=7)
    recent_memes = Meme.objects.filter(
        is_published=True,
        created_at__gte=week_ago
    )
    
    if recent_memes.count() >= 5:
        featured_memes = random.sample(list(recent_memes), 5)
    else:
        featured_memes = list(recent_memes)
    
    # Формируем содержимое письма
    subject = f'Ежедневный дайджест мемов - {datetime.now().strftime("%d.%m.%Y")}'
    
    message = 'Привет! Вот подборка мемов за сегодня:\n\n'
    for i, meme in enumerate(featured_memes, 1):
        message += f'{i}. {meme.title}\n'
        if meme.description:
            message += f'   {meme.description[:100]}...\n'
        message += f'   Автор: {meme.author.username}\n'
        message += f'   Лайков: {meme.likes_count}\n\n'
    
    message += '\nХорошего дня!\nКоманда Memyau'
    
    # Отправляем каждому подписчику
    for user in subscribers:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    
    return f'Отправлено {len(subscribers)} писем'