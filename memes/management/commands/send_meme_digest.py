from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
from memes.models import Meme
from users.models import MemeSubscription, Profile
from datetime import datetime, timedelta
from django.utils import timezone
import random
from django.template.loader import render_to_string

class Command(BaseCommand):
    help = 'Send meme digest to subscribers'
    
    def add_arguments(self, parser):
        parser.add_argument('frequency', type=str, choices=['daily', 'weekly'], 
                          help='Frequency of digest: daily or weekly')
    
    def handle(self, *args, **options):
        frequency = options['frequency']
        self.stdout.write(f'[{timezone.now()}] Starting {frequency} digest sending...')
        
        # Получаем подписчиков с активной подпиской
        subscriptions = MemeSubscription.objects.filter(
            is_active=True,
            frequency=frequency
        ).select_related('user', 'user__profile')
        
        total_subscriptions = subscriptions.count()
        self.stdout.write(f'Found {total_subscriptions} active {frequency} subscriptions')
        
        sent_count = 0
        failed_count = 0
        
        for subscription in subscriptions:
            try:
                # Проверяем email пользователя
                if not subscription.user or not subscription.user.email:
                    self.stdout.write(f'Skipping subscription {subscription.id} - no user or email')
                    failed_count += 1
                    continue
                
                # Проверяем, можно ли отправлять сейчас (упрощенная версия)
                if subscription.last_sent:
                    hours_passed = (timezone.now() - subscription.last_sent).total_seconds() / 3600
                    if frequency == 'daily' and hours_passed < 20:
                        self.stdout.write(f'Skipping {subscription.user.email} - too soon after last send')
                        continue
                    elif frequency == 'weekly' and hours_passed < 6*24:  # 6 дней
                        self.stdout.write(f'Skipping {subscription.user.email} - too soon after last send')
                        continue
                
                success = self.send_digest_to_user(subscription.user, frequency)
                
                if success:
                    subscription.last_sent = timezone.now()
                    subscription.save(update_fields=['last_sent'])
                    sent_count += 1
                    self.stdout.write(f'✓ Sent to {subscription.user.email}')
                else:
                    failed_count += 1
                    self.stdout.write(f'✗ Failed to send to {subscription.user.email}')
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(
                    f'Error sending to {subscription.user.email if subscription.user else "unknown"}: {str(e)}'
                ))
                continue
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully sent {sent_count} {frequency} digests, failed: {failed_count}'
        ))
        return sent_count, failed_count
    
    def send_digest_to_user(self, user, frequency):
        """Отправка дайджеста пользователю"""
        if not user.email:
            self.stdout.write(f'User {user.username} has no email address')
            return False
        
        # Определяем период
        if frequency == 'daily':
            start_date = timezone.now() - timedelta(days=1)
            period_name = 'день'
        else:  # weekly
            start_date = timezone.now() - timedelta(days=7)
            period_name = 'неделю'
        
        # Получаем популярные мемы за период
        recent_memes = Meme.objects.filter(
            is_published=True,
            created_at__gte=start_date
        ).order_by('-likes_count', '-created_at')[:6]
        
        self.stdout.write(f'Found {len(recent_memes)} memes for {user.email}')
        
        # Если недостаточно мемов за период, добавляем случайные популярные
        if len(recent_memes) < 3:
            extra_memes = Meme.objects.filter(
                is_published=True,
            ).exclude(id__in=[m.id for m in recent_memes]) \
             .order_by('-likes_count')[:6-len(recent_memes)]
            recent_memes = list(recent_memes) + list(extra_memes)
            self.stdout.write(f'Added {len(extra_memes)} extra memes')
        
        if not recent_memes:
            self.stdout.write(f'No memes found for {user.email}')
            return False
        
        # Мем дня (случайный из популярных)
        meme_of_the_day = None
        if recent_memes:
            meme_of_the_day = random.choice(list(recent_memes))
            self.stdout.write(f'Meme of the day: {meme_of_the_day.title}')
        
        # Формируем тему письма
        today = timezone.now().date()
        if frequency == 'daily':
            subject = f'📅 Ежедневный дайджест мемов - {today.strftime("%d.%m.%Y")}'
        else:
            subject = f'📊 Еженедельный дайджест мемов - {today.strftime("%d.%m.%Y")}'
        
        # Получаем токен отписки (если есть)
        unsubscribe_token = ''
        try:
            if hasattr(user, 'profile') and user.profile:
                unsubscribe_token = getattr(user.profile, 'unsubscribe_token', '')
        except Exception:
            pass
        
        # Контекст для шаблона
        context = {
            'user': user,
            'frequency': frequency,
            'period_name': period_name,
            'today': today.strftime('%d.%m.%Y'),
            'meme_of_the_day': meme_of_the_day,
            'recent_memes': recent_memes[:4],  # Максимум 4 мема
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            'unsubscribe_url': f'http://localhost:8000/users/unsubscribe/{unsubscribe_token}/' if unsubscribe_token else 'http://localhost:8000/users/settings/',
            'subject': subject,
        }
        
        try:
            # Текстовое содержимое (упрощенное)
            text_content = f"""
Привет, {user.username}!

Ваш {frequency} дайджест мемов за {period_name} - {today.strftime('%d.%m.%Y')}.

{'⭐ Мем дня: ' + meme_of_the_day.title if meme_of_the_day else ''}

🔥 Популярные мемы:
{chr(10).join([f'{i+1}. {meme.title} (👍 {meme.likes_count} лайков)' for i, meme in enumerate(recent_memes[:4])])}

Посмотреть все мемы: {getattr(settings, 'SITE_URL', 'http://localhost:8000')}

Отписаться от рассылки: {f'http://localhost:8000/users/unsubscribe/{unsubscribe_token}/' if unsubscribe_token else 'http://localhost:8000/users/settings/'}

С уважением,
Команда Memeow 🐱
"""
            
            # Рендерим HTML
            html_content = render_to_string('users/emails/meme_digest.html', context)
            
            # Создаем email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL]
            )
            
            email.attach_alternative(html_content, "text/html")
            
            # Добавляем изображения как вложения (если есть изображение мема дня)
            if meme_of_the_day and meme_of_the_day.image:
                try:
                    image_path = meme_of_the_day.image.path
                    with open(image_path, 'rb') as img_file:
                        email.attach(
                            filename=f'meme_of_day_{meme_of_the_day.id}.jpg',
                            content=img_file.read(),
                            mimetype='image/jpeg'
                        )
                    self.stdout.write(f'✓ Image attached for meme {meme_of_the_day.id}')
                except Exception as e:
                    self.stdout.write(f'✗ Could not attach image for meme {meme_of_the_day.id}: {e}')
            
            # Отправляем
            self.stdout.write(f'Attempting to send email to {user.email}')
            result = email.send()
            
            if result == 1:
                self.stdout.write(f'✓ Email sent successfully to {user.email}')
                return True
            else:
                self.stdout.write(f'✗ Email send failed for {user.email}, result: {result}')
                return False
                
        except Exception as e:
            self.stdout.write(f'✗ Email sending error for {user.email}: {str(e)}')
            import traceback
            self.stdout.write(traceback.format_exc())
            return False