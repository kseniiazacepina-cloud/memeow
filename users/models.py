from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    email_subscription = models.BooleanField(default=True)
    unsubscribe_token = models.CharField(max_length=32, unique=True, blank=True, null=True)
    
    def __str__(self):
        return f'Профиль {self.user.username}'
    
    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            import uuid
            self.unsubscribe_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

# Сигнал для автоматического создания профиля при создании пользователя
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class MemeSubscription(models.Model):
    """Модель подписки на рассылку мемов"""
    FREQUENCY_CHOICES = [
        ('daily', 'Ежедневно'),
        ('weekly', 'Еженедельно'),
        ('none', 'Не получать'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('telegram', 'Telegram'),
        ('both', 'Оба способа'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='meme_subscription')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='none')
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='email')
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_sent = models.DateTimeField(null=True, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Подписка {self.user.username} - {self.get_frequency_display()}"
    
    def can_send_now(self):
        """Проверяет, можно ли отправлять рассылку сейчас"""
        if not self.is_active or self.frequency == 'none':
            return False
        
        if not self.last_sent:
            return True
            
        now = timezone.now()
        if self.frequency == 'daily':
            # Проверяем, прошло ли более 24 часов
            return (now - self.last_sent).days >= 1
        else:  # weekly
            # Проверяем, прошло ли более 7 дней
            return (now - self.last_sent).days >= 7


class TelegramConnection(models.Model):
    """Модель для привязки Telegram"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='telegram_connection')
    telegram_chat_id = models.CharField(max_length=100, unique=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)
    verification_code = models.CharField(max_length=10, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def generate_verification_code(self):
        """Генерация кода верификации"""
        import random
        import string
        self.verification_code = ''.join(random.choices(string.digits, k=6))
    
    def __str__(self):
        return f"Telegram {self.user.username} ({self.telegram_username})"