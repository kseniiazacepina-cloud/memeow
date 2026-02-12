from django.test import TestCase
from django.contrib.auth.models import User
from users.models import Profile, MemeSubscription, TelegramConnection
from memes.tests.factories import UserFactory
import uuid


class ProfileModelTest(TestCase):
    """Тесты для модели Profile"""
    
    def setUp(self):
        self.user = UserFactory()
        self.profile = Profile.objects.get(user=self.user)
    
    def test_profile_created_automatically(self):
        """Тест автоматического создания профиля"""
        self.assertIsNotNone(self.profile)
        self.assertEqual(self.profile.user, self.user)
    
    def test_profile_str_method(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.profile), f'Профиль {self.user.username}')
    
    def test_unsubscribe_token_generated(self):
        """Тест генерации токена отписки"""
        self.assertIsNotNone(self.profile.unsubscribe_token)
        self.assertEqual(len(self.profile.unsubscribe_token), 32)
    
    def test_unsubscribe_token_unique(self):
        """Тест уникальности токена отписки"""
        user2 = UserFactory()
        profile2 = Profile.objects.get(user=user2)
        
        self.assertNotEqual(
            self.profile.unsubscribe_token,
            profile2.unsubscribe_token
        )
    
    def test_profile_default_values(self):
        """Тест значений по умолчанию"""
        self.assertTrue(self.profile.email_subscription)
        self.assertIsNone(self.profile.avatar)
        self.assertEqual(self.profile.bio, '')


class MemeSubscriptionModelTest(TestCase):
    """Тесты для модели MemeSubscription"""
    
    def setUp(self):
        self.user = UserFactory()
        self.subscription = MemeSubscription.objects.create(
            user=self.user,
            frequency='daily',
            channel='email',
            is_active=True
        )
    
    def test_subscription_creation(self):
        """Тест создания подписки"""
        self.assertEqual(self.subscription.user, self.user)
        self.assertEqual(self.subscription.frequency, 'daily')
        self.assertTrue(self.subscription.is_active)
    
    def test_subscription_str_method(self):
        """Тест строкового представления"""
        expected = f"Подписка {self.user.username} - Ежедневно"
        self.assertEqual(str(self.subscription), expected)
    
    def test_subscription_default_created_on_user_creation(self):
        """Тест создания подписки по умолчанию при создании пользователя"""
        new_user = UserFactory()
        subscription = MemeSubscription.objects.get(user=new_user)
        
        self.assertEqual(subscription.frequency, 'weekly')
        self.assertEqual(subscription.channel, 'email')
        self.assertTrue(subscription.is_active)
    
    def test_can_send_now_no_last_sent(self):
        """Тест can_send_now когда еще не отправляли"""
        self.assertTrue(self.subscription.can_send_now())
    
    def test_can_send_now_daily(self):
        """Тест can_send_now для ежедневной подписки"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Отправляли 23 часа назад
        self.subscription.last_sent = timezone.now() - timedelta(hours=23)
        self.subscription.save()
        
        self.assertFalse(self.subscription.can_send_now())
        
        # Отправляли 25 часов назад
        self.subscription.last_sent = timezone.now() - timedelta(hours=25)
        self.subscription.save()
        
        self.assertTrue(self.subscription.can_send_now())
    
    def test_can_send_now_weekly(self):
        """Тест can_send_now для еженедельной подписки"""
        self.subscription.frequency = 'weekly'
        
        from django.utils import timezone
        from datetime import timedelta
        
        # Отправляли 6 дней назад
        self.subscription.last_sent = timezone.now() - timedelta(days=6)
        self.subscription.save()
        
        self.assertFalse(self.subscription.can_send_now())
        
        # Отправляли 8 дней назад
        self.subscription.last_sent = timezone.now() - timedelta(days=8)
        self.subscription.save()
        
        self.assertTrue(self.subscription.can_send_now())
    
    def test_can_send_now_inactive(self):
        """Тест can_send_now для неактивной подписки"""
        self.subscription.is_active = False
        self.subscription.save()
        
        self.assertFalse(self.subscription.can_send_now())
    
    def test_can_send_now_none_frequency(self):
        """Тест can_send_now для отключенной рассылки"""
        self.subscription.frequency = 'none'
        self.subscription.save()
        
        self.assertFalse(self.subscription.can_send_now())


class TelegramConnectionModelTest(TestCase):
    """Тесты для модели TelegramConnection"""
    
    def setUp(self):
        self.user = UserFactory()
        self.connection = TelegramConnection.objects.create(
            user=self.user,
            telegram_chat_id='123456789',
            telegram_username='testuser',
            is_verified=False
        )
    
    def test_connection_creation(self):
        """Тест создания подключения"""
        self.assertEqual(self.connection.user, self.user)
        self.assertEqual(self.connection.telegram_chat_id, '123456789')
        self.assertFalse(self.connection.is_verified)
    
    def test_generate_verification_code(self):
        """Тест генерации кода верификации"""
        self.connection.generate_verification_code()
        self.assertIsNotNone(self.connection.verification_code)
        self.assertEqual(len(self.connection.verification_code), 6)
        self.assertTrue(self.connection.verification_code.isdigit())
    
    def test_str_method(self):
        """Тест строкового представления"""
        expected = f"Telegram {self.user.username} (testuser)"
        self.assertEqual(str(self.connection), expected)
    
    def test_unique_telegram_chat_id(self):
        """Тест уникальности chat_id"""
        with self.assertRaises(Exception):
            TelegramConnection.objects.create(
                user=UserFactory(),
                telegram_chat_id='123456789'
            )
    
    def test_unique_verification_code(self):
        """Тест уникальности кода верификации"""
        code = '123456'
        self.connection.verification_code = code
        self.connection.save()
        
        with self.assertRaises(Exception):
            connection2 = TelegramConnection(
                user=UserFactory(),
                telegram_chat_id='987654321',
                verification_code=code
            )
            connection2.save()