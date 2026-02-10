from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from users.models import MemeSubscription, User
from memes.models import Meme
import requests
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Отправляет дайджест мемов подписчикам'
    
    def handle(self, *args, **options):
        self.stdout.write('Начинаю рассылку дайджеста мемов...')
        
        # Получаем активные подписки
        subscriptions = MemeSubscription.objects.filter(
            is_active=True,
            frequency__in=['daily', 'weekly']
        ).select_related('user')
        
        # Получаем мемы для рассылки
        if options['frequency'] == 'daily':
            memes = Meme.objects.filter(
                created_at__date=timezone.now().date(),
                is_published=True
            ).order_by('-likes_count')[:1]  # Лучший мем дня
        else:  # weekly
            week_ago = timezone.now() - timezone.timedelta(days=7)
            memes = Meme.objects.filter(
                created_at__gte=week_ago,
                is_published=True
            ).order_by('-likes_count')[:5]  # Топ-5 мемов недели
        
        for subscription in subscriptions:
            try:
                self.send_digest(subscription, memes)
                subscription.last_sent = timezone.now()
                subscription.save()
                self.stdout.write(f'Отправлено пользователю: {subscription.user.email}')
            except Exception as e:
                logger.error(f'Ошибка отправки для {subscription.user.email}: {e}')
        
        self.stdout.write(self.style.SUCCESS('Рассылка завершена!'))
    
    def send_digest(self, subscription, memes):
        """Отправляет дайджест пользователю"""
        if subscription.channel in ['email', 'both']:
            self.send_email_digest(subscription.user, memes)
        
        if subscription.channel in ['telegram', 'both']:
            self.send_telegram_digest(subscription, memes)
    
    def send_email_digest(self, user, memes):
        """Отправляет дайджест по email"""
        context = {
            'user': user,
            'memes': memes,
            'unsubscribe_url': f'https://memeow.com/unsubscribe/{user.profile.unsubscribe_token}/',
        }
        
        subject = '🎭 Ваша ежедневная доза мемов!' if len(memes) == 1 else '🎭 Топ мемов недели!'
        
        html_message = render_to_string('emails/meme_digest.html', context)
        text_message = render_to_string('emails/meme_digest.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=None,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    
    def send_telegram_digest(self, subscription, memes):
        """Отправляет дайджест в Telegram"""
        if not subscription.telegram_chat_id:
            return
        
        from django.conf import settings
        
        if len(memes) == 1:
            message = "🎭 *Мем дня!*\n\n"
            message += f"{memes[0].title}\n"
            if memes[0].description:
                message += f"{memes[0].description}\n"
            message += f"👍 {memes[0].likes_count} лайков\n\n"
            message += f"Смотреть на сайте: https://memeow.com/meme/{memes[0].id}/"
        else:
            message = "🎭 *Топ-5 мемов недели!*\n\n"
            for i, meme in enumerate(memes, 1):
                message += f"{i}. {meme.title} - 👍 {meme.likes_count}\n"
            message += "\nСмотреть на сайте: https://memeow.com/popular/"
        
        # Отправляем через Telegram Bot API
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = subscription.telegram_chat_id
        
        if bot_token and chat_id:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': False
            }
            
            try:
                response = requests.post(url, json=data, timeout=10)
                if response.status_code != 200:
                    logger.error(f'Ошибка Telegram API: {response.text}')
            except Exception as e:
                logger.error(f'Ошибка отправки в Telegram: {e}')