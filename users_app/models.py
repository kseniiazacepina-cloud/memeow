from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ZODIAC_SIGNS = [
        ('aries', 'Овен'),
        ('taurus', 'Телец'),
        ('gemini', 'Близнецы'),
        ('cancer', 'Рак'),
        ('leo', 'Лев'),
        ('virgo', 'Дева'),
        ('libra', 'Весы'),
        ('scorpio', 'Скорпион'),
        ('sagittarius', 'Стрелец'),
        ('capricorn', 'Козерог'),
        ('aquarius', 'Водолей'),
        ('pisces', 'Рыбы'),
    ]