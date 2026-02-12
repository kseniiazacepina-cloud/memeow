from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from memes.models import Meme, Tag, Like, Favorite
from memes.tests.factories import (
    UserFactory, MemeFactory, TagFactory, LikeFactory, FavoriteFactory
)
from memes.serializers import MemeSerializer, TagSerializer
from django.core.cache import cache
from memes.tests.test_models import TestHelpers
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image


class MemeAPITest(TestCase):
    """Тесты для API мемов"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = TestHelpers.create_user()
        self.meme = TestHelpers.create_meme(
            author=self.user,
            moderation_status='approved',
            is_published=True
        )
        self.tag = TestHelpers.create_tag(name='тест')
        self.meme.tags.add(self.tag)
        
        self.list_url = reverse('meme-list')
        self.detail_url = reverse('meme-detail', kwargs={'pk': self.meme.pk})
    
    def test_get_memes_list(self):
        """Тест получения списка мемов"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_meme_detail(self):
        """Тест получения детальной информации о меме"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.meme.title)
    
    def test_create_meme_unauthorized(self):
        """Тест создания мема без авторизации"""
        data = {
            'title': 'Новый мем',
            'description': 'Описание'
        }
        response = self.client.post(self.list_url, data)
        # API возвращает 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_meme_authorized(self):
        """Тест создания мема с авторизацией"""
        self.client.force_authenticate(user=self.user)
        
        # Создаем тестовое изображение
        file = BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'jpeg')
        file.seek(0)
        image_file = SimpleUploadedFile('test.jpg', file.read(), content_type='image/jpeg')
        
        data = {
            'title': 'Новый мем',
            'description': 'Описание',
            'image': image_file,
            'tag_ids': [self.tag.id]
        }
        
        response = self.client.post(self.list_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_filter_by_tag(self):
        """Тест фильтрации по тегу"""
        response = self.client.get(self.list_url, {'tag': self.tag.slug})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_search_memes(self):
        """Тест поиска мемов"""
        response = self.client.get(self.list_url, {'search': self.meme.title[:5]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_sort_memes(self):
        """Тест сортировки мемов"""
        meme2 = MemeFactory(is_published=True, likes_count=100)
        meme3 = MemeFactory(is_published=True, likes_count=50)
        
        response = self.client.get(self.list_url, {'sort': '-likes_count'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['id'], meme2.id)
    
    def test_random_meme(self):
        """Тест получения случайного мема"""
        url = reverse('meme-random')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
    
    def test_meme_of_the_day(self):
        """Тест получения мема дня"""
        url = reverse('meme-meme-of-the-day')
        
        # Очищаем кэш
        cache.clear()
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что повторный запрос возвращает тот же мем
        response2 = self.client.get(url)
        self.assertEqual(response.data['id'], response2.data['id'])
    
    def test_like_meme(self):
        """Тест лайка мема через API"""
        self.client.force_authenticate(user=self.user)
        url = reverse('meme-like', kwargs={'pk': self.meme.pk})
        
        initial_likes = self.meme.likes_count
        
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['liked'])
        self.assertEqual(response.data['likes_count'], initial_likes + 1)
        
        # Проверяем, что повторный запрос убирает лайк
        response2 = self.client.post(url, {})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertFalse(response2.data['liked'])
        self.assertEqual(response2.data['likes_count'], initial_likes)
    
    def test_favorite_meme(self):
        """Тест добавления в избранное через API"""
        self.client.force_authenticate(user=self.user)
        url = reverse('meme-favorite', kwargs={'pk': self.meme.pk})
        
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['favorited'])
        
        # Проверяем удаление из избранного
        response2 = self.client.post(url, {})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertFalse(response2.data['favorited'])


class StatsAPITest(APITestCase):
    """Тесты для API статистики"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.url = reverse('stats-popular')
        
        # Создаем популярные мемы
        self.popular_meme1 = MemeFactory(
            is_published=True,
            likes_count=100,
            views_count=1000
        )
        self.popular_meme2 = MemeFactory(
            is_published=True,
            likes_count=50,
            views_count=500
        )
    
    def test_get_popular_stats(self):
        """Тест получения популярной статистики"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertIn('popular_memes', response.data)
        self.assertIn('popular_tags', response.data)
        self.assertIn('active_users', response.data)
        
        # Проверяем сортировку популярных мемов
        popular_memes = response.data['popular_memes']
        self.assertGreater(
            popular_memes[0]['likes_count'],
            popular_memes[1]['likes_count']
        )


class LikeAPITest(APITestCase):
    """Тесты для API лайков"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.meme = MemeFactory(is_published=True)
        self.like = LikeFactory(user=self.user, meme=self.meme)
        
        self.url = reverse('like-list')
    
    def test_get_user_likes(self):
        """Тест получения лайков пользователя"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['meme'], self.meme.id)
    
    def test_create_like(self):
        """Тест создания лайка"""
        self.client.force_authenticate(user=self.user)
        
        # Удаляем существующий лайк
        self.like.delete()
        
        data = {'meme': self.meme.id}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)