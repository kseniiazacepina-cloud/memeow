from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify

class Tag(models.Model):
    """Модель тега для классификации мемов"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Название тега')
    slug = models.SlugField(max_length=60, unique=True, blank=True, verbose_name='URL-идентификатор')

    def save(self, *args, **kwargs):
        """Автоматическое создание slug при сохранении"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

class Meme(models.Model):
    """Основная модель мема"""
    title = models.CharField(max_length=200, verbose_name='Название мема')
    image = models.ImageField(
        upload_to='memes/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        verbose_name='Изображение'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memes', verbose_name='Автор')
    tags = models.ManyToManyField(Tag, related_name='memes', blank=True, verbose_name='Теги')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    views_count = models.PositiveIntegerField(default=0, verbose_name='Количество просмотров')
    likes_count = models.PositiveIntegerField(default=0, verbose_name='Количество лайков')
    is_published = models.BooleanField(default=True, verbose_name='Опубликован')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Мем'
        verbose_name_plural = 'Мемы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-likes_count']),
        ]

class Like(models.Model):
    """Модель лайка (связь пользователь-мем)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    meme = models.ForeignKey(Meme, on_delete=models.CASCADE, related_name='like_records')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'meme')  # Один лайк от пользователя на мем
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'

class Favorite(models.Model):
    """Модель избранного (связь пользователь-мем)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    meme = models.ForeignKey(Meme, on_delete=models.CASCADE, related_name='favorite_records')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'meme')  # Один раз в избранном
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        