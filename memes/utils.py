from django.utils import timezone
from .models import Notification

def send_moderation_notification(meme, moderator):
    """Отправить уведомление автору о результате модерации"""
    if meme.moderation_status == 'approved':
        Notification.objects.create(
            user=meme.author,
            notification_type='meme_approved',
            title='Ваш мем одобрен!',
            message=f'Ваш мем "{meme.title}" был одобрен модератором и опубликован на сайте.',
            related_meme=meme
        )
    elif meme.moderation_status == 'rejected':
        Notification.objects.create(
            user=meme.author,
            notification_type='meme_rejected',
            title='Ваш мем отклонен',
            message=f'Ваш мем "{meme.title}" был отклонен. Причина: {meme.moderation_comment or "Не указана"}',
            related_meme=meme
        )

def send_report_notification(meme, reporter):
    """Отправить уведомление автору о жалобе"""
    Notification.objects.create(
        user=meme.author,
        notification_type='meme_reported',
        title='На ваш мем пожаловались',
        message=f'На ваш мем "{meme.title}" поступила жалоба. Мем будет проверен модератором.',
        related_meme=meme
    )

def send_report_resolution_notification(report, moderator):
    """Отправить уведомление о рассмотрении жалобы"""
    if report.reporter:
        Notification.objects.create(
            user=report.reporter,
            notification_type='report_resolved',
            title='📋 Ваша жалоба рассмотрена',
            message=f'Ваша жалоба на мем "{report.meme.title}" была рассмотрена модератором.',
            related_report=report
        )