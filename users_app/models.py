from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    newsletter_subscription = models.BooleanField(
        _('newsletter subscription'),
        default=True,
        help_text=_('Подпишитесь на ежедневную рассылку мемов')
    )
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        default='avatars/default.png',
        blank=True
    )
    bio = models.TextField(_('bio'), max_length=500, blank=True)
    favorite_tags = models.ManyToManyField(
        'memes.Tag',
        related_name='users_with_favorite',
        blank=True
    )

    class Meta:
       verbose_name = _('user')
       verbose_name_plural = _('users')

    def __str__(self):
        return self.username
    
    @property
    def favorite_memes_count(self):
        return self.favorites.count()
    
    @property
    def liked_memes_count(self):
        return self.likes.count()