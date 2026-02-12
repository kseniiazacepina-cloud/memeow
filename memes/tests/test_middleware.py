from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from memes.middleware import UserActivityMiddleware
from memes.models import UserActivity
from memes.tests.factories import UserFactory, MemeFactory
from memes.tests.test_models import TestHelpers


class UserActivityMiddlewareTest(TestCase):
    """Тесты для middleware активности пользователей"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = TestHelpers.create_user()
        self.middleware = UserActivityMiddleware(lambda req: None)
    
    def test_log_authenticated_user_activity(self):
        """Тест логирования активности авторизованного пользователя"""
        request = self.factory.get('/meme/1/')
        request.user = self.user
        
        self.middleware.log_activity(request, '127.0.0.1')
        
        activity = UserActivity.objects.first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.action_type, 'view_meme')
    
    def test_log_anonymous_user_activity(self):
        """Тест логирования активности анонимного пользователя"""
        request = self.factory.get('/meme/1/')
        request.user = AnonymousUser()
        
        self.middleware.log_activity(request, '127.0.0.1')
        
        activity = UserActivity.objects.first()
        self.assertIsNotNone(activity)
        self.assertIsNone(activity.user)
        self.assertEqual(activity.action_type, 'view_meme')
    
    def test_get_action_type_login(self):
        """Тест определения типа действия - вход"""
        action = self.middleware.get_action_type('/login/', 'POST')
        self.assertEqual(action, 'login')
    
    def test_get_action_type_view_meme(self):
        """Тест определения типа действия - просмотр мема"""
        action = self.middleware.get_action_type('/meme/123/', 'GET')
        self.assertEqual(action, 'view_meme')
    
    def test_get_action_type_add_meme(self):
        """Тест определения типа действия - добавление мема"""
        action = self.middleware.get_action_type('/add_meme/', 'POST')
        self.assertEqual(action, 'add_meme')
    
    def test_get_action_type_moderation(self):
        """Тест определения типа действия - модерация"""
        action = self.middleware.get_action_type('/moderation_queue/', 'GET')
        self.assertEqual(action, 'moderate')
    
    def test_get_action_type_admin(self):
        """Тест определения типа действия - админка"""
        action = self.middleware.get_action_type('/admin/', 'GET')
        self.assertEqual(action, 'admin_action')
    
    def test_get_client_ip_forwarded(self):
        """Тест получения IP с X-Forwarded-For"""
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR='192.168.1.1, 10.0.0.1')
        ip = self.middleware.get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_client_ip_remote_addr(self):
        """Тест получения IP с REMOTE_ADDR"""
        request = self.factory.get('/', REMOTE_ADDR='10.0.0.1')
        ip = self.middleware.get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')

    def test_no_log_for_non_tracked_paths(self):
        """Тест отсутствия логирования для неотслеживаемых путей"""
        request = self.factory.get('/')
        request.user = self.user
        
        self.middleware.log_activity(request, '127.0.0.1')
        
        activity = UserActivity.objects.first()
        self.assertIsNone(activity)