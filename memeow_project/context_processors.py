from memes.models import Notification

def unread_notifications(request):
    """Добавляет количество непрочитанных уведомлений в контекст"""
    if request.user.is_authenticated:
        try:
            unread_count = Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).count()
            return {'unread_notifications_count': unread_count}
        except:
            # Если что-то пошло не так, возвращаем 0
            return {'unread_notifications_count': 0}
    return {'unread_notifications_count': 0}