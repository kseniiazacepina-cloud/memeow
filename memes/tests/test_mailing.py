from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from io import StringIO
from memes.management.commands.send_meme_digest import Command
from memes.tests.factories import UserFactory, MemeFactory
from users.models import MemeSubscription, Profile
from memes.tests.test_models import TestHelpers
from memes.models import Meme


class MailingTest(TestCase):
    """Тесты для рассылки мемов"""
    
    def setUp(self):
        # Создаем пользователя
        self.user = TestHelpers.create_user(email='test@example.com')
        self.profile = Profile.objects.get(user=self.user)
        
        # Создаем или обновляем подписку
        self.subscription, created = MemeSubscription.objects.get_or_create(
            user=self.user,
            defaults={
                'frequency': 'daily',
                'channel': 'email',
                'is_active': True
            }
        )
        
        if not created:
            self.subscription.frequency = 'daily'
            self.subscription.is_active = True
            self.subscription.save()
        
        # Создаем мемы
        Meme.objects.all().delete()
        for i in range(3):
            TestHelpers.create_meme(
                is_published=True,
                moderation_status='approved',
                created_at=timezone.now() - timedelta(hours=i)
            )
    
    def test_send_daily_digest_command(self):
        """Тест команды отправки ежедневного дайджеста"""
        out = StringIO()
        # Важно: команда не должна возвращать кортеж
        call_command('send_meme_digest', 'daily', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Starting daily digest sending...', output)
        self.assertIn('Found 1 active daily subscriptions', output)
        
        # Проверяем отправку письма
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Ежедневный дайджест мемов', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to[0], 'test@example.com')
    
    def test_send_digest_inactive_subscription(self):
        """Тест отправки дайджеста с неактивной подпиской"""
        self.subscription.is_active = False
        self.subscription.save()
        
        out = StringIO()
        call_command('send_meme_digest', 'daily', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Found 0 active daily subscriptions', output)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_digest_no_memes(self):
        """Тест отправки дайджеста без мемов"""
        Meme.objects.all().delete()
        
        # Создаем нового пользователя и подписку для этого теста
        user2 = TestHelpers.create_user(email='test2@example.com')
        subscription2, created = MemeSubscription.objects.get_or_create(
            user=user2,
            defaults={
                'frequency': 'daily',
                'channel': 'email',
                'is_active': True
            }
        )
        
        out = StringIO()
        call_command('send_meme_digest', 'daily', stdout=out)
        
        output = out.getvalue()
        # Должен быть хотя бы 1 подписчик
        self.assertIn('Found 1 active daily subscriptions', output)
        # Но письмо не должно отправиться из-за отсутствия мемов
        self.assertEqual(len(mail.outbox), 0)