from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from memes.tests.factories import UserFactory, MemeFactory, FavoriteFactory
from users.models import Profile, MemeSubscription
import json


class RegisterViewTest(TestCase):
    """Тесты для регистрации пользователей"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('register')
    
    def test_register_page_status_code(self):
        """Тест доступности страницы регистрации"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
    
    def test_register_valid_user(self):
        """Тест регистрации валидного пользователя"""
        response = self.client.post(self.url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        
        # Проверяем создание пользователя
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Проверяем создание профиля
        user = User.objects.get(username='newuser')
        self.assertTrue(Profile.objects.filter(user=user).exists())
        
        # Проверяем создание подписки
        self.assertTrue(MemeSubscription.objects.filter(user=user).exists())
        
        # Проверяем отправку приветственного письма
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Добро пожаловать на Memeow', mail.outbox[0].subject)
    
    def test_register_duplicate_username(self):
        """Тест регистрации с существующим именем"""
        UserFactory(username='existinguser')
        
        response = self.client.post(self.url, {
            'username': 'existinguser',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 
                           'Пользователь с таким именем уже существует.')
    
    def test_register_duplicate_email(self):
        """Тест регистрации с существующим email"""
        UserFactory(email='existing@example.com')
        
        response = self.client.post(self.url, {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 
                           'Этот email уже зарегистрирован')
    
    def test_register_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        response = self.client.post(self.url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password2', 
                           'Введенные пароли не совпадают.')


class ProfileViewTest(TestCase):
    """Тесты для страницы профиля"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.profile = Profile.objects.get(user=self.user)
        self.url = reverse('profile')
    
    def test_profile_requires_login(self):
        """Тест, что профиль требует авторизации"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_profile_authenticated(self):
        """Тест профиля для авторизованного пользователя"""
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertEqual(response.context['profile_user'], self.user)
    
    def test_profile_with_username(self):
        """Тест профиля другого пользователя"""
        other_user = UserFactory()
        
        self.client.login(username=self.user.username, password='testpass123')
        url = reverse('user_profile', kwargs={'username': other_user.username})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile_user'], other_user)
    
    def test_profile_nonexistent_user(self):
        """Тест профиля несуществующего пользователя"""
        self.client.login(username=self.user.username, password='testpass123')
        url = reverse('user_profile', kwargs={'username': 'nonexistent'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_profile_context(self):
        """Тест контекста страницы профиля"""
        self.client.login(username=self.user.username, password='testpass123')
        
        # Создаем мемы и избранное
        meme1 = MemeFactory(author=self.user, is_published=True)
        meme2 = MemeFactory(author=self.user, is_published=True)
        favorite = FavoriteFactory(user=self.user, meme=meme1)
        
        response = self.client.get(self.url)
        
        self.assertEqual(len(response.context['user_memes']), 2)
        self.assertEqual(len(response.context['user_favorites']), 1)
        self.assertEqual(response.context['memes_count'], 2)
        self.assertEqual(response.context['likes_received'], 
                       meme1.likes_count + meme2.likes_count)


class SettingsViewTest(TestCase):
    """Тесты для страницы настроек"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory(
            first_name='Иван',
            last_name='Иванов',
            email='ivan@example.com'
        )
        self.profile = Profile.objects.get(user=self.user)
        self.url = reverse('settings')
    
    def test_settings_requires_login(self):
        """Тест, что настройки требуют авторизации"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
    
    def test_settings_get(self):
        """Тест GET запроса настроек"""
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/settings.html')
        self.assertIn('user_form', response.context)
        self.assertIn('profile_form', response.context)
    
    def test_settings_post_valid(self):
        """Тест POST запроса с валидными данными"""
        self.client.login(username=self.user.username, password='testpass123')
        
        response = self.client.post(self.url, {
            'username': self.user.username,
            'email': 'updated@example.com',
            'first_name': 'Петр',
            'last_name': 'Петров',
            'bio': 'Новая биография',
            'email_subscription': 'on',
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile'))
        
        # Проверяем обновление данных
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.first_name, 'Петр')
        self.assertEqual(self.user.last_name, 'Петров')
        self.assertEqual(self.profile.bio, 'Новая биография')
        self.assertTrue(self.profile.email_subscription)
    
    def test_settings_post_invalid(self):
        """Тест POST запроса с невалидными данными"""
        self.client.login(username=self.user.username, password='testpass123')
        
        response = self.client.post(self.url, {
            'username': '',  # Пустое имя
            'email': 'invalid-email',  # Невалидный email
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user_form'].is_valid())
        self.assertFalse(response.context['profile_form'].is_valid())


class FavoritesViewTest(TestCase):
    """Тесты для страницы избранного"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.url = reverse('favorites')
        
        # Создаем избранные мемы
        self.meme1 = MemeFactory(is_published=True)
        self.meme2 = MemeFactory(is_published=True)
        self.meme3 = MemeFactory(is_published=True)
        
        self.favorite1 = FavoriteFactory(user=self.user, meme=self.meme1)
        self.favorite2 = FavoriteFactory(user=self.user, meme=self.meme2)
    
    def test_favorites_requires_login(self):
        """Тест, что избранное требует авторизации"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
    
    def test_favorites_authenticated(self):
        """Тест избранного для авторизованного пользователя"""
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/favorites.html')
        
        favorite_memes = response.context['favorite_memes']
        self.assertEqual(len(favorite_memes), 2)
        self.assertIn(self.meme1, favorite_memes)
        self.assertIn(self.meme2, favorite_memes)
        self.assertNotIn(self.meme3, favorite_memes)
    
    def test_favorites_exclude_unpublished(self):
        """Тест исключения неопубликованных мемов из избранного"""
        unpublished_meme = MemeFactory(is_published=False)
        FavoriteFactory(user=self.user, meme=unpublished_meme)
        
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.get(self.url)
        
        favorite_memes = response.context['favorite_memes']
        self.assertEqual(len(favorite_memes), 2)
        self.assertNotIn(unpublished_meme, favorite_memes)


class SubscriptionTest(TestCase):
    """Тесты для подписки на рассылку"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.url = reverse('save_subscription_ajax')
    
    def test_save_subscription_requires_login(self):
        """Тест, что сохранение подписки требует авторизации"""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 403)
    
    def test_save_subscription_json(self):
        """Тест сохранения подписки через JSON"""
        self.client.login(username=self.user.username, password='testpass123')
        
        data = {
            'channel': 'telegram',
            'frequency': 'daily'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Проверяем обновление подписки
        subscription = MemeSubscription.objects.get(user=self.user)
        self.assertEqual(subscription.channel, 'telegram')
        self.assertEqual(subscription.frequency, 'daily')
        self.assertTrue(subscription.is_active)
    
    def test_save_subscription_form_data(self):
        """Тест сохранения подписки через FormData"""
        self.client.login(username=self.user.username, password='testpass123')
        
        response = self.client.post(self.url, {
            'channel': 'email',
            'frequency': 'none'
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        subscription = MemeSubscription.objects.get(user=self.user)
        self.assertEqual(subscription.frequency, 'none')
        self.assertFalse(subscription.is_active)
    
    def test_unsubscribe_with_token(self):
        """Тест отписки по токену"""
        profile = Profile.objects.get(user=self.user)
        url = reverse('unsubscribe_meme', kwargs={'token': profile.unsubscribe_token})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
        
        subscription = MemeSubscription.objects.get(user=self.user)
        self.assertFalse(subscription.is_active)
    
    def test_unsubscribe_invalid_token(self):
        """Тест отписки с невалидным токеном"""
        url = reverse('unsubscribe_meme', kwargs={'token': 'invalidtoken123'})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Подписка не найдена', str(messages[0]))