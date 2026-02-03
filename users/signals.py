from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создание профиля при создании пользователя"""
    if created:
        Profile.objects.create(user=instance)
        # Отправляем приветственное письмо
        send_welcome_email(instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохранение профиля при сохранении пользователя"""
    instance.profile.save()

def send_welcome_email(user):
    """Отправка приветственного письма новому пользователю"""
    subject = 'Добро пожаловать на Memyau!'
    message = f'''
    Привет, {user.username}!
    
    Добро пожаловать на Memyau - лучшую платформу для мемов и анекдотов!
    
    Вы можете:
    - Добавлять свои мемы
    - Лайкать понравившиеся
    - Сохранять в избранное
    - Подписаться на рассылку
    
    Начните использовать все возможности прямо сейчас!
    
    С уважением,
    Команда Memyau
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )