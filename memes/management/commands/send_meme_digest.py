from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from memes.models import Meme
from users.models import MemeSubscription, Profile
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Send meme digest to subscribers'
    
    def add_arguments(self, parser):
        parser.add_argument('frequency', type=str, choices=['daily', 'weekly'], 
                          help='Frequency of digest: daily or weekly')
    
    def handle(self, *args, **options):
        frequency = options['frequency']
        
        # Получаем подписчиков с активной подпиской
        subscriptions = MemeSubscription.objects.filter(
            is_active=True,
            frequency=frequency
        )
        
        count = 0
        for subscription in subscriptions:
            if self.send_digest_to_user(subscription.user, frequency):
                count += 1
                subscription.last_sent = datetime.now()
                subscription.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully sent {count} {frequency} digests'
        ))
    
    def send_digest_to_user(self, user, frequency):
        """Отправка дайджеста пользователю"""
        # Определяем период
        if frequency == 'daily':
            start_date = datetime.now() - timedelta(days=1)
        else:  # weekly
            start_date = datetime.now() - timedelta(days=7)
        
        # Получаем популярные мемы за период
        recent_memes = Meme.objects.filter(
            is_published=True,
            created_at__gte=start_date
        ).order_by('-likes_count')[:5]
        
        if not recent_memes:
            return False
        
        # Формируем тему письма
        if frequency == 'daily':
            subject = f'Ежедневный дайджест мемов - {datetime.now().strftime("%d.%m.%Y")}'
        else:
            subject = f'Еженедельный дайджест мемов - {datetime.now().strftime("%d.%m.%Y")}'
        
        # Формируем текст письма
        message = f'Привет, {user.username}!\n\n'
        message += f'Вот подборка популярных мемов за последний период:\n\n'
        
        for i, meme in enumerate(recent_memes, 1):
            message += f'{i}. {meme.title}\n'
            if meme.description:
                message += f'   {meme.description[:100]}...\n'
            message += f'   Автор: {meme.author.username}\n'
            message += f'   Лайков: {meme.likes_count}\n'
            message += f'   Ссылка: http://localhost:8000/meme/{meme.id}/\n\n'
        
        message += '\n---\n'
        message += f'Если вы хотите изменить настройки подписки, перейдите в настройки профиля.\n'
        message += f'Отписаться от рассылки: http://localhost:8000/unsubscribe/{user.profile.unsubscribe_token}/\n\n'
        message += 'Хорошего дня!\nКоманда Memeow'
        
        try:
            # Отправляем email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error sending to {user.email}: {str(e)}'
            ))
            return False