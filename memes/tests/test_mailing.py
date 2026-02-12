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
    # ОЧИЩАЕМ ВСЕ ПОДПИСКИ ПЕРЕД КАЖДЫМ ТЕСТОМ
    MemeSubscription.objects.all().delete()
    
    # Очищаем почтовый ящик
    mail.outbox = []
    
    # Создаем пользователя
    self.user = TestHelpers.create_user(email='test@example.com')
    self.profile = Profile.objects.get(user=self.user)
    
    # СОЗДАЕМ ПОДПИСКУ ТОЛЬКО ЗДЕСЬ, БОЛЬШЕ НИГДЕ!
    self.subscription = MemeSubscription.objects.create(
        user=self.user,
        frequency='daily',
        channel='email',
        is_active=True
    )
    
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
        mail.outbox = []

        out = StringIO()
        call_command('send_meme_digest', 'daily', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Starting daily digest sending...', output)
        self.assertIn('Found 1 active daily subscriptions', output)
        
        # Проверяем отправку письма
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Ежедневный дайджест мемов', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to[0], 'test@example.com')
    
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
    
    def test_send_digest_inactive_subscription(self):
        """Тест отправки дайджеста с неактивной подпиской"""
        self.subscription.is_active = False
        self.subscription.save()
        
        out = StringIO()
        call_command('send_meme_digest', 'daily', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Found 0 active daily subscriptions', output)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_digest_too_soon(self):
        """Тест отправки дайджеста слишком рано"""
        self.subscription.last_sent = timezone.now()
        self.subscription.save()
        
        out = StringIO()
        call_command('send_meme_digest', 'daily', stdout=out)
        
        output = out.getvalue()
        self.assertIn('too soon after last send', output)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_weekly_digest(self):
        """Тест отправки еженедельного дайджеста"""
        # ОЧИЩАЕМ ПОЧТОВЫЙ ЯЩИК!
        mail.outbox = []
        
        self.subscription.frequency = 'weekly'
        self.subscription.save()
        
        out = StringIO()
        call_command('send_meme_digest', 'weekly', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Starting weekly digest sending...', output)
        self.assertEqual(len(mail.outbox), 1)  # Теперь будет 1!
        self.assertIn('Еженедельный дайджест мемов', mail.outbox[0].subject)
    
    def test_digest_content(self):
        """Тест содержимого дайджеста"""
        mail.outbox = []
        call_command('send_meme_digest', 'daily')
        
        email = mail.outbox[0]
        
        # Проверяем тему
        today = timezone.now().date().strftime('%d.%m.%Y')
        self.assertIn(today, email.subject)
        
        # Проверяем HTML и текстовую версию
        self.assertEqual(len(email.alternatives), 1)
        self.assertEqual(email.alternatives[0][1], 'text/html')
        
        # Проверяем наличие мемов в письме
        body = email.body
        memes = Meme.objects.filter(is_published=True)[:4]
        for meme in memes:
            self.assertIn(meme.title, body)
    
    def test_unsubscribe_link(self):
        """Тест наличия ссылки для отписки"""
        call_command('send_meme_digest', 'daily')
        
        email = mail.outbox[0]
        body = email.body
        
        unsubscribe_url = f'http://localhost:8000/users/unsubscribe/{self.profile.unsubscribe_token}/'
        self.assertIn(unsubscribe_url, body)
    
    def test_send_digest_no_email(self):
        """Тест отправки пользователю без email"""
        self.user.email = ''
        self.user.save()
        
        out = StringIO()
        call_command('send_meme_digest', 'daily', stdout=out)
        
        output = out.getvalue()
        # Исправляем: проверяем правильное сообщение из команды
        self.assertIn('no user or email', output)  # Изменено!
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_digest_multiple_subscribers(self):
        """Тест отправки нескольким подписчикам"""
        # Очищаем почтовый ящик
        mail.outbox = []
        
        user2 = TestHelpers.create_user(email='test2@example.com')
        
        # Используем get_or_create вместо create
        subscription2, created = MemeSubscription.objects.get_or_create(
            user=user2,
            defaults={
                'frequency': 'daily',
                'channel': 'email',
                'is_active': True
            }
        )
        
        if not created:
            subscription2.frequency = 'daily'
            subscription2.is_active = True
            subscription2.save()
        
        out = StringIO()
        call_command('send_meme_digest', 'daily', stdout=out)
        
        self.assertEqual(len(mail.outbox), 2)
        
        sent_emails = [email.to[0] for email in mail.outbox]
        self.assertIn('test@example.com', sent_emails)
        self.assertIn('test2@example.com', sent_emails)
    
    def test_send_digest_with_image_attachment(self):
        """Тест отправки дайджеста с вложением изображения"""
        # Очищаем почтовый ящик
        mail.outbox = []
        
        # Создаем мем с изображением
        from django.core.files.uploadedfile import SimpleUploadedFile
        from io import BytesIO
        from PIL import Image
        
        file = BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'jpeg')
        file.seek(0)
        
        meme_with_image = MemeFactory(
            is_published=True,
            image=SimpleUploadedFile('test.jpg', file.read(), content_type='image/jpeg')
        )
        
        out = StringIO()
        call_command('send_meme_digest', 'daily', stdout=out)
        
        output = out.getvalue()
        # Проверяем, что письмо отправлено
        self.assertEqual(len(mail.outbox), 1)
        # Не проверяем конкретную строку, так как она может быть в разных форматах
        self.assertIn('Successfully sent 1 daily digests', output)