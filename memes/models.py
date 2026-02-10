from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL')
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Дата создания',
        null=True,  # ← Добавьте null=True для существующих записей
        blank=True  # ← Добавьте blank=True
    )
    
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        
        # Устанавливаем created_at для новых записей
        if not self.pk and not self.created_at:
            from django.utils import timezone
            self.created_at = timezone.now()
        
        super().save(*args, **kwargs)

class Meme(models.Model):
    MODERATION_STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]
    
    # Основные поля
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='memes/%Y/%m/%d/', verbose_name='Изображение')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memes', verbose_name='Автор')
    tags = models.ManyToManyField(Tag, related_name='memes', blank=True, verbose_name='Теги')
    views_count = models.IntegerField(default=0, verbose_name='Просмотры')
    likes_count = models.IntegerField(default=0, verbose_name='Лайки')
    
    # Модерация
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS_CHOICES,
        default='pending',
        verbose_name='Статус модерации'
    )
    moderation_comment = models.TextField(blank=True, verbose_name='Комментарий модератора')
    moderated_at = models.DateTimeField(null=True, blank=True, verbose_name='Время модерации')
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_memes',
        verbose_name='Модератор'
    )
    
    is_published = models.BooleanField(default=False, verbose_name='Опубликовано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Мем'
        verbose_name_plural = 'Мемы'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('meme_detail', kwargs={'pk': self.pk})
    
    def get_status_color(self):
        """Цвет для отображения статуса"""
        colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
        return colors.get(self.moderation_status, 'secondary')
    
    def get_status_icon(self):
        """Иконка для статуса"""
        icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌'
        }
        return icons.get(self.moderation_status, '❓')

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    meme = models.ForeignKey(Meme, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'meme']
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
    
    def __str__(self):
        return f"{self.user.username} лайкнул {self.meme.title}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    meme = models.ForeignKey(Meme, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'meme']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
    
    def __str__(self):
        return f"{self.user.username} добавил в избранное {self.meme.title}"

class Report(models.Model):
    """Жалобы на мемы"""
    REASON_CHOICES = [
        ('spam', 'Спам'),
        ('offensive', 'Оскорбительный контент'),
        ('copyright', 'Нарушение авторских прав'),
        ('violence', 'Насилие'),
        ('other', 'Другое'),
    ]
    
    meme = models.ForeignKey(Meme, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reports_made')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True, verbose_name='Описание проблемы')
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False, verbose_name='Рассмотрено')
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_reports',
        verbose_name='Рассмотрел'
    )
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Время рассмотрения')
    resolution_notes = models.TextField(blank=True, verbose_name='Примечания модератора')
    
    class Meta:
        verbose_name = 'Жалоба'
        verbose_name_plural = 'Жалобы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Жалоба на '{self.meme.title}' от {self.reporter.username}"
    
    def resolve(self, moderator, notes=''):
        """Пометить жалобу как рассмотренную"""
        self.is_resolved = True
        self.resolved_by = moderator
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()
        
        # Отправляем уведомление автору мема
        Notification.objects.create(
            user=self.meme.author,
            notification_type='report_resolved',
            title=f'Жалоба на мем "{self.meme.title}" рассмотрена',
            message=f'Ваша жалоба на мем "{self.meme.title}" была рассмотрена модератором.',
            link=f'/memes/{self.meme.id}/'
        )

class Notification(models.Model):
    """Уведомления для пользователей"""
    NOTIFICATION_TYPES = [
        ('meme_approved', 'Мем одобрен'),
        ('meme_rejected', 'Мем отклонен'),
        ('meme_reported', 'На ваш мем пожаловались'),
        ('report_resolved', 'Жалоба рассмотрена'),
        ('like', 'Лайк'),
        ('favorite', 'Добавление в избранное'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_meme = models.ForeignKey(Meme, on_delete=models.CASCADE, null=True, blank=True)
    related_report = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=500, blank=True, null=True)  # URL для перехода
    related_meme = models.ForeignKey(Meme, on_delete=models.SET_NULL, 
                                     null=True, blank=True, 
                                     related_name='notifications')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
    
    def __str__(self):
        return f"Уведомление для {self.user.username}: {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class UserActivity(models.Model):
    """Модель для отслеживания активности пользователей"""
    
    ACTION_TYPES = [
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
        ('register', 'Регистрация'),
        ('view_meme', 'Просмотр мема'),
        ('like_meme', 'Лайк мема'),
        ('unlike_meme', 'Убрал лайк'),
        ('favorite_meme', 'Добавил в избранное'),
        ('unfavorite_meme', 'Удалил из избранного'),
        ('add_meme', 'Добавил мем'),
        ('edit_meme', 'Редактировал мем'),
        ('delete_meme', 'Удалил мем'),
        ('report_meme', 'Пожаловался на мем'),
        ('search', 'Поиск'),
        ('view_profile', 'Просмотр профиля'),
        ('moderate', 'Модерация'),
        ('admin_action', 'Админ действие'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='activities',
        null=True,  # Для анонимных действий
        blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField(blank=True)
    
    # Связи с другими моделями (опционально)
    meme = models.ForeignKey(
        'Meme', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='activities'
    )
    target_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='targeted_activities'
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        username = self.user.username if self.user else 'Аноним'
        return f"{username} - {self.get_action_type_display()} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    class Meta:
        verbose_name = 'Активность пользователя'
        verbose_name_plural = 'Активность пользователей'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]