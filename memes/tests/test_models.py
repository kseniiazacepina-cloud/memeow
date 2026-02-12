from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from memes.models import Meme, Tag, Like, Favorite, Report, Notification, UserActivity
from memes.tests.factories import (
    UserFactory, MemeFactory, TagFactory, LikeFactory, 
    FavoriteFactory, ReportFactory, NotificationFactory, UserActivityFactory
)
from users.models import Profile
import random
import string
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

class TestHelpers:
    """Вспомогательные методы для тестов"""
    
    @staticmethod
    def create_user(username=None, email=None, password='testpass123'):
        if not username:
            username = f'testuser_{random.randint(1000, 9999)}'
        if not email:
            email = f'{username}@example.com'
        return User.objects.create_user(username=username, email=email, password=password)
    
    @staticmethod
    def create_tag(name=None):
        if not name:
            name = f'tag_{random.randint(1000, 9999)}'
        tag = Tag.objects.create(name=name)
        return tag
    
    @staticmethod
    def create_test_image():
        file = BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'jpeg')
        file.seek(0)
        return SimpleUploadedFile('test.jpg', file.read(), content_type='image/jpeg')
    
    @staticmethod
    def create_meme(author=None, **kwargs):
        if not author:
            author = TestHelpers.create_user()
        
        defaults = {
            'title': f'Test Meme {random.randint(1000, 9999)}',
            'description': 'Test description',
            'image': TestHelpers.create_test_image(),
            'author': author,
            'is_published': True,
            'moderation_status': 'approved',
            'views_count': 0,
            'likes_count': 0,
        }
        defaults.update(kwargs)
        
        return Meme.objects.create(**defaults)
    
    @staticmethod
    def create_like(user, meme):
        like, created = Like.objects.get_or_create(user=user, meme=meme)
        return like
    
    @staticmethod
    def create_favorite(user, meme):
        favorite, created = Favorite.objects.get_or_create(user=user, meme=meme)
        return favorite
    
    @staticmethod
    def create_report(meme, reporter, **kwargs):
        defaults = {
            'meme': meme,
            'reporter': reporter,
            'reason': 'spam',
            'description': 'Test report',
            'is_resolved': False,
        }
        defaults.update(kwargs)
        return Report.objects.create(**defaults)
    
    @staticmethod
    def create_notification(user, **kwargs):
        defaults = {
            'user': user,
            'notification_type': 'meme_approved',
            'title': 'Test Notification',
            'message': 'Test message',
            'is_read': False,
        }
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)
    
    @staticmethod
    def create_user_activity(user, **kwargs):
        defaults = {
            'user': user,
            'action_type': 'view_meme',
            'description': 'Test activity',
            'ip_address': '127.0.0.1',
            'user_agent': 'test-agent',
        }
        defaults.update(kwargs)
        return UserActivity.objects.create(**defaults)

class TagModelTest(TestCase):
    """Тесты для модели Tag"""
    
    def setUp(self):
        self.tag = TestHelpers.create_tag(name='котики')
    
    def test_tag_creation(self):
        self.assertEqual(self.tag.name, 'котики')
        self.assertEqual(self.tag.slug, 'котики')
    
    def test_tag_str_method(self):
        self.assertEqual(str(self.tag), 'котики')
    
    def test_tag_slug_generation(self):
        tag = TestHelpers.create_tag(name='Смешные Котики!')
        self.assertEqual(tag.slug, 'смешные-котики')
    
    def test_tag_created_at_auto_set(self):
        """Тест автоматической установки даты создания"""
        self.assertIsNotNone(self.tag.created_at)
    
    def test_tag_unique_name(self):
        with self.assertRaises(Exception):
            TestHelpers.create_tag(name='котики')


class MemeModelTest(TestCase):
    """Тесты для модели Meme"""
    
    def setUp(self):
        self.user = TestHelpers.create_user()
        self.meme = TestHelpers.create_meme(
            author=self.user,
            moderation_status='pending',
            is_published=False
        )
        self.tag1 = TestHelpers.create_tag(name='юмор')
        self.tag2 = TestHelpers.create_tag(name='жизнь')
        # Очищаем теги перед добавлением
        self.meme.tags.clear()
        self.meme.tags.add(self.tag1, self.tag2)
    
    def test_meme_creation(self):
        self.assertIsNotNone(self.meme.title)
        self.assertEqual(self.meme.author, self.user)
        self.assertEqual(self.meme.moderation_status, 'pending')
        self.assertFalse(self.meme.is_published)
    
    def test_meme_str_method(self):
        self.assertEqual(str(self.meme), self.meme.title)
    
    def test_meme_get_absolute_url(self):
        url = self.meme.get_absolute_url()
        self.assertEqual(url, f'/meme/{self.meme.pk}/')
    
    def test_meme_status_color(self):
        self.meme.moderation_status = 'pending'
        self.assertEqual(self.meme.get_status_color(), 'warning')
        
        self.meme.moderation_status = 'approved'
        self.assertEqual(self.meme.get_status_color(), 'success')
        
        self.meme.moderation_status = 'rejected'
        self.assertEqual(self.meme.get_status_color(), 'danger')
    
    def test_meme_status_icon(self):
        """Тест иконки статуса"""
        self.meme.moderation_status = 'pending'
        self.assertEqual(self.meme.get_status_icon(), '⧖')
        
        self.meme.moderation_status = 'approved'
        self.assertEqual(self.meme.get_status_icon(), '✔')
        
        self.meme.moderation_status = 'rejected'
        self.assertEqual(self.meme.get_status_icon(), '✖')
    
    def test_meme_tags_relation(self):
        # Очищаем и добавляем заново для чистоты теста
        self.meme.tags.clear()
        self.meme.tags.add(self.tag1, self.tag2)
        self.assertEqual(self.meme.tags.count(), 2)
        self.assertIn(self.tag1, self.meme.tags.all())
        self.assertIn(self.tag2, self.meme.tags.all())
    
    def test_meme_ordering(self):
        """Тест сортировки по дате создания"""
        meme1 = MemeFactory(created_at=timezone.now() - timedelta(days=2))
        meme2 = MemeFactory(created_at=timezone.now() - timedelta(days=1))
        
        memes = Meme.objects.all()
        self.assertGreater(memes[0].created_at, memes[1].created_at)


class LikeModelTest(TestCase):
    """Тесты для модели Like"""
    
    def setUp(self):
        self.user = UserFactory()
        self.meme = MemeFactory()
        self.like = LikeFactory(user=self.user, meme=self.meme)
    
    def test_like_creation(self):
        """Тест создания лайка"""
        self.assertEqual(self.like.user, self.user)
        self.assertEqual(self.like.meme, self.meme)
    
    def test_like_unique_together(self):
        """Тест уникальности пары пользователь-мем"""
        with self.assertRaises(Exception):
            LikeFactory(user=self.user, meme=self.meme)
    
    def test_like_str_method(self):
        """Тест строкового представления"""
        expected = f"{self.user.username} лайкнул {self.meme.title}"
        self.assertEqual(str(self.like), expected)
    
    def test_like_cascade_delete(self):
        """Тест каскадного удаления при удалении пользователя"""
        user_id = self.user.id
        self.user.delete()
        self.assertEqual(Like.objects.filter(user_id=user_id).count(), 0)


class FavoriteModelTest(TestCase):
    """Тесты для модели Favorite"""
    
    def setUp(self):
        self.user = UserFactory()
        self.meme = MemeFactory()
        self.favorite = FavoriteFactory(user=self.user, meme=self.meme)
    
    def test_favorite_creation(self):
        """Тест создания избранного"""
        self.assertEqual(self.favorite.user, self.user)
        self.assertEqual(self.favorite.meme, self.meme)
    
    def test_favorite_unique_together(self):
        """Тест уникальности пары пользователь-мем"""
        with self.assertRaises(Exception):
            FavoriteFactory(user=self.user, meme=self.meme)
    
    def test_favorite_str_method(self):
        """Тест строкового представления"""
        expected = f"{self.user.username} добавил в избранное {self.meme.title}"
        self.assertEqual(str(self.favorite), expected)


class ReportModelTest(TestCase):
    """Тесты для модели Report"""
    
    def setUp(self):
        self.user = UserFactory()
        self.meme = MemeFactory()
        self.report = ReportFactory(
            reporter=self.user, 
            meme=self.meme,
            reason='offensive',
            description='Очень оскорбительно'
        )
        self.moderator = UserFactory(is_staff=True)
    
    def test_report_creation(self):
        """Тест создания жалобы"""
        self.assertEqual(self.report.reporter, self.user)
        self.assertEqual(self.report.meme, self.meme)
        self.assertEqual(self.report.reason, 'offensive')
        self.assertFalse(self.report.is_resolved)
    
    def test_report_str_method(self):
        """Тест строкового представления"""
        expected = f"Жалоба на '{self.meme.title}' от {self.user.username}"
        self.assertEqual(str(self.report), expected)
    
    def test_report_resolve(self):
        """Тест разрешения жалобы"""
        self.report.resolve(self.moderator, 'Жалоба рассмотрена')
        
        self.assertTrue(self.report.is_resolved)
        self.assertEqual(self.report.resolved_by, self.moderator)
        self.assertIsNotNone(self.report.resolved_at)
        self.assertEqual(self.report.resolution_notes, 'Жалоба рассмотрена')
        
        # Проверяем создание уведомления
        from memes.models import Notification
        notification = Notification.objects.filter(
            user=self.meme.author,
            notification_type='report_resolved'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn(self.meme.title, notification.message)


class NotificationModelTest(TestCase):
    """Тесты для модели Notification"""
    
    def setUp(self):
        self.user = UserFactory()
        self.notification = NotificationFactory(user=self.user)
    
    def test_notification_creation(self):
        """Тест создания уведомления"""
        self.assertEqual(self.notification.user, self.user)
        self.assertFalse(self.notification.is_read)
    
    def test_notification_str_method(self):
        """Тест строкового представления"""
        expected = f"Уведомление для {self.user.username}: {self.notification.title}"
        self.assertEqual(str(self.notification), expected)
    
    def test_notification_mark_as_read(self):
        """Тест отметки уведомления как прочитанного"""
        self.notification.mark_as_read()
        self.assertTrue(self.notification.is_read)
    
    def test_notification_ordering(self):
        """Тест сортировки уведомлений"""
        notif1 = NotificationFactory(created_at=timezone.now() - timedelta(days=1))
        notif2 = NotificationFactory(created_at=timezone.now())
        
        notifications = Notification.objects.all()
        self.assertGreater(notifications[0].created_at, notifications[1].created_at)


class UserActivityModelTest(TestCase):
    """Тесты для модели UserActivity"""
    
    def setUp(self):
        self.user = UserFactory()
        self.meme = MemeFactory()
        self.activity = UserActivityFactory(
            user=self.user,
            action_type='view_meme',
            meme=self.meme
        )
    
    def test_activity_creation(self):
        """Тест создания активности"""
        self.assertEqual(self.activity.user, self.user)
        self.assertEqual(self.activity.action_type, 'view_meme')
        self.assertEqual(self.activity.meme, self.meme)
    
    def test_activity_str_method(self):
        """Тест строкового представления"""
        date_str = self.activity.created_at.strftime('%d.%m.%Y %H:%M')
        expected = f"{self.user.username} - Просмотр мема - {date_str}"
        self.assertEqual(str(self.activity), expected)
    
    def test_activity_anonymous_user(self):
        """Тест активности анонимного пользователя"""
        activity = UserActivityFactory(user=None, action_type='search')
        self.assertIsNone(activity.user)
        self.assertEqual(str(activity).startswith('Аноним'), True)