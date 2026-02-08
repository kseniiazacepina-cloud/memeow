from django.core.management.base import BaseCommand
from memes.models import Tag, Meme
from django.contrib.auth.models import User
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Создает базовые теги и тестовые мемы'
    
    def handle(self, *args, **kwargs):
        # 1. Создаем пользователя если нет
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Создан тестовый пользователь'))
        
        # 2. Создаем базовые теги
        base_tags = ['котики', 'собаки', 'юмор', 'мемы', 'программирование', 
                    'IT', 'работа', 'учеба', 'игры', 'фильмы']
        
        for tag_name in base_tags:
            slug = slugify(tag_name)
            tag, created = Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': tag_name}
            )
            if created:
                self.stdout.write(f'Создан тег: {tag_name}')
        
        # 3. Проверяем, есть ли мемы
        if Meme.objects.count() == 0:
            self.stdout.write(self.style.WARNING('Нет мемов в базе'))
            self.stdout.write('Создайте мемы через форму на сайте')
        else:
            # Показываем статистику
            self.stdout.write(f'\nВсего мемов: {Meme.objects.count()}')
            self.stdout.write(f'Всего тегов: {Tag.objects.count()}')
            
            # Проверяем теги у мемов
            memes_without_tags = []
            for meme in Meme.objects.all():
                if meme.tags.count() == 0:
                    memes_without_tags.append(meme)
            
            if memes_without_tags:
                self.stdout.write(self.style.WARNING(f'\nМемы без тегов: {len(memes_without_tags)}'))
                for meme in memes_without_tags[:5]:
                    self.stdout.write(f'  - {meme.title}')
            else:
                self.stdout.write(self.style.SUCCESS('\nУ всех мемов есть теги!'))