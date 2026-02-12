from django.test import TestCase
from django.contrib.auth.models import User
from memes.utils import (
    send_moderation_notification, send_report_notification,
    send_report_resolution_notification, log_user_activity,
    track_like_activity, track_report_activity, track_moderation_activity
)
from memes.models import Notification, UserActivity
from memes.tests.factories import UserFactory, MemeFactory, ReportFactory


class UtilsTest(TestCase):
    """Тесты для утилит"""
    
    def setUp(self):
        self.author = UserFactory()
        self.moderator = UserFactory(is_staff=True)
        self.meme = MemeFactory(author=self.author)
        self.reporter = UserFactory()
    
    def test_send_moderation_notification_approved(self):
        """Тест отправки уведомления об одобрении"""
        self.meme.moderation_status = 'approved'
        
        send_moderation_notification(self.meme, self.moderator)
        
        notification = Notification.objects.filter(
            user=self.author,
            notification_type='meme_approved'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.related_meme, self.meme)
        self.assertIn(self.meme.title, notification.message)
    
    def test_send_moderation_notification_rejected(self):
        """Тест отправки уведомления об отклонении"""
        self.meme.moderation_status = 'rejected'
        self.meme.moderation_comment = 'Не соответствует правилам'
        
        send_moderation_notification(self.meme, self.moderator)
        
        notification = Notification.objects.filter(
            user=self.author,
            notification_type='meme_rejected'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn(self.meme.moderation_comment, notification.message)
    
    def test_send_report_notification(self):
        """Тест отправки уведомления о жалобе"""
        send_report_notification(self.meme, self.reporter)
        
        notification = Notification.objects.filter(
            user=self.author,
            notification_type='meme_reported'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.related_meme, self.meme)
    
    def test_send_report_resolution_notification(self):
        """Тест отправки уведомления о рассмотрении жалобы"""
        report = ReportFactory(reporter=self.reporter, meme=self.meme)
        
        send_report_resolution_notification(report, self.moderator)
        
        notification = Notification.objects.filter(
            user=self.reporter,
            notification_type='report_resolved'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.related_report, report)
    
    def test_log_user_activity(self):
        """Тест логирования активности пользователя"""
        activity = log_user_activity(
            user=self.author,
            action_type='test_action',
            description='Тестовое действие',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.user, self.author)
        self.assertEqual(activity.action_type, 'test_action')
        self.assertEqual(activity.ip_address, '127.0.0.1')
    
    def test_track_like_activity(self):
        """Тест отслеживания лайка"""
        track_like_activity(self.reporter, self.meme, action='like')
        
        activity = UserActivity.objects.filter(
            user=self.reporter,
            action_type='like_meme'
        ).first()
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.meme, self.meme)
    
    def test_track_report_activity(self):
        """Тест отслеживания жалобы"""
        track_report_activity(self.reporter, self.meme)
        
        activity = UserActivity.objects.filter(
            user=self.reporter,
            action_type='report_meme'
        ).first()
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.meme, self.meme)
    
    def test_track_moderation_activity(self):
        """Тест отслеживания модерации"""
        track_moderation_activity(self.moderator, self.meme, 'Одобрил')
        
        activity = UserActivity.objects.filter(
            user=self.moderator,
            action_type='moderate'
        ).first()
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.meme, self.meme)
        self.assertIn('Одобрил', activity.description)