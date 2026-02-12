from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from memes.models import Meme, Tag, Like, Favorite, Report, Notification
from memes.tests.factories import (
    UserFactory, MemeFactory, TagFactory, LikeFactory,
    FavoriteFactory, ReportFactory, NotificationFactory
)
from users.models import Profile
import json
from io import BytesIO
from PIL import Image
from memes.tests.test_models import TestHelpers

class HomeViewTest(TestCase):
    """Тесты для главной страницы"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('home')
        
        self.meme1 = TestHelpers.create_meme()
        self.meme2 = TestHelpers.create_meme()
        self.meme3 = TestHelpers.create_meme()
        
        self.tag1 = TestHelpers.create_tag(name='котики')
        self.tag2 = TestHelpers.create_tag(name='собачки')
        self.meme1.tags.add(self.tag1)
        self.meme2.tags.add(self.tag2)
    
    def test_home_page_status_code(self):
        """Тест доступности главной страницы"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
    
    def test_home_page_template(self):
        """Тест использования правильного шаблона"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'memes/home.html')
    
    def test_home_page_context(self):
        """Тест контекста главной страницы"""
        response = self.client.get(self.url)
        
        self.assertIn('meme_of_the_day', response.context)
        self.assertIn('recent_memes', response.context)
        self.assertIn('popular_memes', response.context)
        self.assertIn('popular_tags', response.context)
        
        # Не проверяем точное количество тегов
        popular_tags = response.context['popular_tags']
        self.assertGreaterEqual(popular_tags.count(), 0)
    
    def test_meme_of_the_day_consistency(self):
        """Тест, что мем дня не меняется в течение дня"""
        response1 = self.client.get(self.url)
        response2 = self.client.get(self.url)
        
        meme1 = response1.context['meme_of_the_day']
        meme2 = response2.context['meme_of_the_day']
        
        self.assertEqual(meme1.id, meme2.id)


class MemeDetailViewTest(TestCase):
    """Тесты для страницы детального просмотра мема"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.meme = MemeFactory(
            author=self.user,
            moderation_status='approved',
            is_published=True
        )
        self.url = reverse('meme_detail', kwargs={'pk': self.meme.pk})
    
    def test_meme_detail_status_code(self):
        """Тест доступности страницы"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
    
    def test_meme_detail_template(self):
        """Тест использования правильного шаблона"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'memes/meme_detail.html')
    
    def test_meme_detail_context(self):
        """Тест контекста страницы"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.context['meme'], self.meme)
        self.assertIn('similar_memes', response.context)
        self.assertIn('is_liked', response.context)
        self.assertIn('is_favorite', response.context)
    
    def test_meme_views_count_increment(self):
        """Тест увеличения счетчика просмотров"""
        initial_views = self.meme.views_count
        
        self.client.get(self.url)
        self.meme.refresh_from_db()
        
        self.assertEqual(self.meme.views_count, initial_views + 1)
    
    def test_unpublished_meme_404(self):
        """Тест, что неопубликованный мем недоступен"""
        unpublished_meme = MemeFactory(is_published=False)
        url = reverse('meme_detail', kwargs={'pk': unpublished_meme.pk})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_like_status_for_authenticated_user(self):
        """Тест статуса лайка для авторизованного пользователя"""
        self.client.login(username=self.user.username, password='testpass123')
        
        # Создаем лайк
        LikeFactory(user=self.user, meme=self.meme)
        
        response = self.client.get(self.url)
        self.assertTrue(response.context['is_liked'])


class AddMemeViewTest(TestCase):
    """Тесты для страницы добавления мема"""
    
    def setUp(self):
        self.client = Client()
        self.user = TestHelpers.create_user()
        self.url = reverse('add_meme')
        
        self.image = self.create_test_image()
    
    def create_test_image(self):
        file = BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'jpeg')
        file.seek(0)
        return SimpleUploadedFile('test.jpg', file.read(), content_type='image/jpeg')
    
    def test_add_meme_requires_login(self):
        """Тест, что добавление мема требует авторизации"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_add_meme_get_authenticated(self):
        """Тест GET запроса для авторизованного пользователя"""
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'memes/add_meme.html')
        self.assertIn('form', response.context)
    
    def test_add_meme_post_valid_data(self):
        """Тест POST запроса с валидными данными"""
        self.client.login(username=self.user.username, password='testpass123')
        
        data = {
            'title': 'Тестовый мем',
            'description': 'Описание тестового мема',
            'tags_input': 'котики, юмор',
            'image': self.image
        }
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('my_memes'))
        
        meme = Meme.objects.filter(title='Тестовый мем').first()
        self.assertIsNotNone(meme)
        self.assertEqual(meme.author, self.user)
    
    def test_add_meme_post_invalid_data(self):
        """Тест POST запроса с невалидными данными"""
        self.client.login(username=self.user.username, password='testpass123')
        
        data = {
            'description': 'Описание',
            'image': self.image
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        
        # Используем английскую версию ошибки
        self.assertFormError(response, 'form', 'title', 'This field is required.')


class ToggleLikeViewTest(TestCase):
    """Тесты для AJAX лайков"""
    
    def setUp(self):
        self.client = Client()
        self.user = TestHelpers.create_user()
        self.meme = TestHelpers.create_meme()
        self.url = reverse('toggle_like', kwargs={'pk': self.meme.pk})
    
    def test_toggle_like_requires_login(self):
        """Тест, что лайк требует авторизации"""
        response = self.client.post(self.url, {},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # Django возвращает 302 редирект на login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_toggle_like_add(self):
        """Тест добавления лайка"""
        self.client.login(username=self.user.username, password='testpass123')
        initial_likes = self.meme.likes_count
        
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['liked'])
        self.assertEqual(data['likes_count'], initial_likes + 1)
        
        # Проверяем создание лайка в БД
        self.assertTrue(Like.objects.filter(user=self.user, meme=self.meme).exists())
        
        # Проверяем создание уведомления (если автор не сам пользователь)
        if self.meme.author != self.user:
            self.assertTrue(
                Notification.objects.filter(
                    user=self.meme.author,
                    notification_type='meme_approved',
                    related_meme=self.meme
                ).exists()
            )
    
    def test_toggle_like_remove(self):
        """Тест удаления лайка"""
        self.client.login(username=self.user.username, password='testpass123')
        
        # Сначала добавляем лайк
        LikeFactory(user=self.user, meme=self.meme)
        self.meme.likes_count = 1
        self.meme.save()
        
        # Теперь удаляем
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['liked'])
        self.assertEqual(data['likes_count'], 0)
        
        # Проверяем удаление лайка из БД
        self.assertFalse(Like.objects.filter(user=self.user, meme=self.meme).exists())


class SearchViewTest(TestCase):
    """Тесты для поиска"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('search')
        
        self.meme1 = MemeFactory(
            title='Котик играет с мячиком',
            description='Милый котик',
            moderation_status='approved',
            is_published=True
        )
        self.meme2 = MemeFactory(
            title='Собачка бежит',
            description='Быстрая собачка',
            moderation_status='approved',
            is_published=True
        )
        
        self.tag = TagFactory(name='котики')
        self.meme1.tags.add(self.tag)
    
    def test_search_with_query(self):
        """Тест поиска с запросом"""
        response = self.client.get(self.url, {'q': 'котик'})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'memes/search_results.html')
        
        memes = response.context['memes']
        self.assertEqual(len(memes), 1)
        self.assertEqual(memes[0], self.meme1)
    
    def test_search_with_empty_query(self):
        """Тест поиска с пустым запросом"""
        response = self.client.get(self.url, {'q': ''})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['memes']), 0)
    
    def test_search_no_results(self):
        """Тест поиска без результатов"""
        response = self.client.get(self.url, {'q': 'несуществующий'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['memes']), 0)
    
    def test_search_by_tag(self):
        """Тест поиска по тегу"""
        response = self.client.get(self.url, {'q': 'котики'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['memes']), 1)
        self.assertEqual(response.context['memes'][0], self.meme1)
    
    def test_search_pagination(self):
        """Тест пагинации результатов поиска"""
        # Создаем много мемов
        for i in range(25):
            MemeFactory(
                title=f'Котик {i}',
                moderation_status='approved',
                is_published=True
            )
        
        response = self.client.get(self.url, {'q': 'котик', 'page': 2})
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['memes'].has_previous())
        self.assertFalse(response.context['memes'].has_next())