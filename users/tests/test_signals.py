from django.test import TestCase
from django.contrib.auth.models import User
from users.models import Profile, MemeSubscription
from users.signals import send_welcome_email
from memes.tests.factories import UserFactory
from django.core import mail


class SignalsTest(TestCase):
    """Тесты для сигналов пользователей"""
    
    def test_profile_created_on_user_creation(self):
        """Тест создания профиля при создании пользователя"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertTrue(Profile.objects.filter(user=user).exists())
        profile = Profile.objects.get(user=user)
        self.assertIsNotNone(profile.unsubscribe_token)
        self.assertTrue(profile.email_subscription)
    
    def test_subscription_created_on_user_creation(self):
        """Тест создания подписки при создании пользователя"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertTrue(MemeSubscription.objects.filter(user=user).exists())
        subscription = MemeSubscription.objects.get(user=user)
        self.assertEqual(subscription.frequency, 'weekly')
        self.assertEqual(subscription.channel, 'email')
        self.assertTrue(subscription.is_active)
    
    def test_profile_updated_on_user_update(self):
        """Тест обновления профиля при обновлении пользователя"""
        user = UserFactory(first_name='Иван', last_name='Иванов')
        profile = Profile.objects.get(user=user)
        
        user.first_name = 'Петр'
        user.last_name = 'Петров'
        user.save()
        
        profile.refresh_from_db()
        self.assertEqual(profile.user.first_name, 'Петр')
        self.assertEqual(profile.user.last_name, 'Петров')
    
    def test_send_welcome_email(self):
        """Тест отправки приветственного письма"""
        user = UserFactory(email='test@example.com')
        send_welcome_email(user)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertEqual(email.subject, 'Добро пожаловать на Memeow!')
        self.assertEqual(email.to, ['test@example.com'])
        self.assertIn(user.username, email.body)
        self.assertIn('Memeow', email.body)
    
    def test_profile_already_exists(self):
        """Тест, что профиль не создается повторно"""
        user = UserFactory()
        
        # Пытаемся создать профиль еще раз
        Profile.objects.get_or_create(user=user)
        
        # Проверяем, что профиль только один
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)