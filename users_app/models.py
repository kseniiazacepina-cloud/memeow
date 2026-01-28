from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    email_subscription = models.BooleanField(default=False)
    telegram_subscription = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)