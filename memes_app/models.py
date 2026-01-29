from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model

User = get_user_model()

class Meme(models.Model):
    title = models.CharField(_('title'), max_length=200)
    image = models.ImageField(
        _('image'),
        upload_to='memes_app/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        ]
    )
    description = models.TextField(_('description'), blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memes',
        verbose_name=_('author')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    views_count = models.PositiveIntegerField(_('views count'), default=0)
    likes_count = models.PositiveIntegerField(_('likes count'), default=0)
    is_published = models.BooleanField(_('is published'), default=True)
    tags = models.ManyToManyField(Tag, related_name='memes', verbose_name=_('tags'))
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('meme')
        verbose_name_plural = _('memes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['views_count']),
            models.Index(fields=['likes_count']),
        ]
    
    def __str__(self):
        return self.title
    
    def increment_views(self): #Увеличение счетчика просмотров
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def update_likes_count(self): #Обновление счетчика лайков
        self.likes_count = self.likes.count()
        self.save(update_fields=['likes_count'])


class Tag(models.Model):
    name = models.CharField(_('name'), max_length=50, unique=True)
    slug = models.SlugField(_('slug'), max_length=50, unique=True)
    description = models.TextField(_('description'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']

    def __str__(self):
        return self.name

class Like(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_('user')
    )
    meme = models.ForeignKey(
        Meme,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_('meme')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        unique_together = ['user', 'meme']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} likes {self.meme.title}'

class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('user')
    )
    meme = models.ForeignKey(
        Meme,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('meme')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('favorite')
        verbose_name_plural = _('favorites')
        unique_together = ['user', 'meme']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} favorited {self.meme.title}'