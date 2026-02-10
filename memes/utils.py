from django.utils import timezone
from .models import Notification, UserActivity

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

def log_user_activity(user, action_type, description='', ip_address=None, 
                      user_agent='', meme=None, target_user=None):
    """
    Утилита для ручного логирования активности пользователя
    """
    try:
        activity = UserActivity.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            action_type=action_type,
            description=description,
            meme=meme,
            target_user=target_user,
            created_at=timezone.now()
        )
        return activity
    except Exception as e:
        print(f"Error logging activity: {e}")
        return None

# Пример использования в других местах:
def track_like_activity(user, meme, action='like'):
    """Отслеживание лайков/дизлайков"""
    action_type = 'like_meme' if action == 'like' else 'unlike_meme'
    description = f"{'Лайкнул' if action == 'like' else 'Убрал лайк'} мем: {meme.title}"
    log_user_activity(user, action_type, description, meme=meme)

def track_report_activity(user, meme):
    """Отслеживание жалоб"""
    description = f"Пожаловался на мем: {meme.title}"
    log_user_activity(user, 'report_meme', description, meme=meme)

def track_moderation_activity(moderator, meme, action):
    """Отслеживание действий модерации"""
    description = f"{action} мем: {meme.title}"
    log_user_activity(moderator, 'moderate', description, meme=meme)