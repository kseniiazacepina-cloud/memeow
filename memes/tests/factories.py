import factory 
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image
import random
import string
from memes.models import Meme, Tag, Like, Favorite, Report, Notification, UserActivity
from users.models import Profile, MemeSubscription, TelegramConnection


class UserFactory(DjangoModelFactory):
    """Фабрика для создания пользователей"""
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class ProfileFactory(DjangoModelFactory):
    """Фабрика для создания профилей"""
    class Meta:
        model = Profile
    
    user = factory.SubFactory(UserFactory)
    bio = factory.Faker('text', max_nb_chars=200)
    email_subscription = factory.Faker('boolean')
    
    @factory.lazy_attribute
    def avatar(self):
        """Создает тестовое изображение"""
        file = BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'png')
        file.seek(0)
        return ContentFile(file.read(), 'test_avatar.png')


class TagFactory(DjangoModelFactory):
    """Фабрика для создания тегов"""
    class Meta:
        model = Tag
    
    name = factory.Sequence(lambda n: f'tag{n}')
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(' ', '-'))
    created_at = factory.Faker('date_time_this_year')


class MemeFactory(DjangoModelFactory):
    """Фабрика для создания мемов"""
    class Meta:
        model = Meme
    
    title = factory.Sequence(lambda n: f'Meme {n}')
    description = factory.Faker('text', max_nb_chars=200)
    author = factory.SubFactory(UserFactory)
    views_count = factory.Faker('random_int', min=0, max=1000)
    likes_count = factory.Faker('random_int', min=0, max=500)
    moderation_status = random.choice(['pending', 'approved', 'rejected'])
    is_published = factory.LazyAttribute(lambda o: o.moderation_status == 'approved')
    created_at = factory.Faker('date_time_this_year')
    
    @factory.lazy_attribute
    def image(self):
        """Создает тестовое изображение"""
        file = BytesIO()
        image = Image.new('RGB', (800, 600), 'blue')
        image.save(file, 'jpeg')
        file.seek(0)
        return ContentFile(file.read(), 'test_meme.jpg')
    
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Добавляет теги к мему"""
        if not create:
            return
        
        if extracted:
            for tag in extracted:
                self.tags.add(tag)
        else:
            # Создаем случайные теги
            for i in range(random.randint(1, 3)):
                tag = TagFactory()
                self.tags.add(tag)


class LikeFactory(DjangoModelFactory):
    """Фабрика для создания лайков"""
    class Meta:
        model = Like
    
    user = factory.SubFactory(UserFactory)
    meme = factory.SubFactory(MemeFactory)
    created_at = factory.Faker('date_time_this_year')


class FavoriteFactory(DjangoModelFactory):
    """Фабрика для создания избранного"""
    class Meta:
        model = Favorite
    
    user = factory.SubFactory(UserFactory)
    meme = factory.SubFactory(MemeFactory)
    created_at = factory.Faker('date_time_this_year')


class ReportFactory(DjangoModelFactory):
    """Фабрика для создания жалоб"""
    class Meta:
        model = Report
    
    meme = factory.SubFactory(MemeFactory)
    reporter = factory.SubFactory(UserFactory)
    reason = random.choice(['spam', 'offensive', 'copyright', 'violence', 'other'])
    description = factory.Faker('text', max_nb_chars=200)
    is_resolved = False
    created_at = factory.Faker('date_time_this_year')


class NotificationFactory(DjangoModelFactory):
    """Фабрика для создания уведомлений"""
    class Meta:
        model = Notification
    
    user = factory.SubFactory(UserFactory)
    notification_type = random.choice([
        'meme_approved', 'meme_rejected', 'meme_reported', 
        'report_resolved', 'like', 'favorite'
    ])
    title = factory.Sequence(lambda n: f'Notification {n}')
    message = factory.Faker('text', max_nb_chars=100)
    is_read = False
    created_at = factory.Faker('date_time_this_year')


class UserActivityFactory(DjangoModelFactory):
    """Фабрика для создания активности пользователей"""
    class Meta:
        model = UserActivity
    
    user = factory.SubFactory(UserFactory)
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    action_type = random.choice([
        'login', 'logout', 'view_meme', 'like_meme', 
        'add_meme', 'report_meme', 'moderate'
    ])
    description = factory.Faker('text', max_nb_chars=100)
    created_at = factory.Faker('date_time_this_year')


class MemeSubscriptionFactory(DjangoModelFactory):
    """Фабрика для создания подписок на рассылку"""
    class Meta:
        model = MemeSubscription
    
    user = factory.SubFactory(UserFactory)
    frequency = random.choice(['daily', 'weekly', 'none'])
    channel = random.choice(['email', 'telegram', 'both'])
    is_active = True
    subscribed_at = factory.Faker('date_time_this_year')


class TelegramConnectionFactory(DjangoModelFactory):
    """Фабрика для создания Telegram подключений"""
    class Meta:
        model = TelegramConnection
    
    user = factory.SubFactory(UserFactory)
    telegram_chat_id = factory.Sequence(lambda n: f'{n}{n}{n}{n}{n}')
    telegram_username = factory.Sequence(lambda n: f'user{n}')
    verification_code = factory.LazyFunction(lambda: ''.join(random.choices(string.digits, k=6)))
    is_verified = False
    created_at = factory.Faker('date_time_this_year')