from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создает профиль только для нового пользователя"""
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs): 
    """Сохраняет профиль при сохранении пользователя"""
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # Если профиля нет, создаем его
        Profile.objects.create(user=instance)

def send_welcome_email(user):
    """Отправка приветственного письма новому пользователю"""
    subject = 'Добро пожаловать на Memeow!'
    message = f'''
    Привет, {user.username}!
    
    Добро пожаловать на Memeow - лучшую платформу для мемов и анекдотов!
    
    Вы можете:
    - Добавлять свои мемы
    - Лайкать понравившиеся
    - Сохранять в избранное
    - Подписаться на рассылку
    
    Начните использовать все возможности прямо сейчас!
    
    С уважением,
    Команда Memeow
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )