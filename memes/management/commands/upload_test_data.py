import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from memes.models import Meme, Tag
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
import random
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Загружает тестовые мемы с тегами'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить все существующие мемы перед загрузкой',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Очистка существующих мемов...")
            Meme.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Мемы очищены"))
        
        self.upload_test_memes()
    
    def upload_test_memes(self):
        """Основная функция загрузки"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("НАЧАЛО ЗАГРУЗКИ ТЕСТОВЫХ ДАННЫХ")
        self.stdout.write("="*50)
        
        # 1. Пользователь
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Создан пользователь: {user.username}"))
        
        # 2. Создаем теги
        base_tags = [
            'котики', 'собаки', 'животные', 'юмор', 'мемы',
            'программирование', 'IT', 'работа', 'офис', 'учеба',
            'игры', 'кино', 'фильмы', 'музыка', 'спорт', 'еда'
        ]
        
        tags_dict = {}
        for tag_name in base_tags:
            slug = slugify(tag_name, allow_unicode=True)
            if not slug:
                slug = f"tag-{hash(tag_name)}"
            
            tag, created = Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': tag_name}
            )
            tags_dict[tag_name] = tag
        
        self.stdout.write(self.style.SUCCESS(f"Создано тегов: {len(tags_dict)}"))
        
        # 3. Тестовые мемы
        test_memes = [
            {
                'title': 'Программист и котик',
                'description': 'Когда твой код review делает кот',
                'tags': ['котики', 'программирование', 'юмор']
            },
            {
                'title': 'Утро понедельника',
                'description': 'Когда нужно идти на работу',
                'tags': ['работа', 'офис', 'юмор']
            },
            {
                'title': 'Баги в продакшене',
                'description': 'Критические ошибки в пятницу вечером',
                'tags': ['программирование', 'работа', 'IT']
            },
            {
                'title': 'Собеседование',
                'description': 'Когда спрашивают про алгоритмы',
                'tags': ['работа', 'программирование', 'учеба']
            },
            {
                'title': 'Гит vs Гитхаб',
                'description': 'Разница очевидна',
                'tags': ['программирование', 'IT', 'юмор']
            },
            {
                'title': 'Собака-разработчик',
                'description': 'Лучший друг программиста',
                'tags': ['собаки', 'программирование', 'юмор']
            },
            {
                'title': 'Кофе и код',
                'description': 'Идеальное сочетание',
                'tags': ['работа', 'программирование', 'юмор']
            },
            {
                'title': 'Дедлайн',
                'description': 'Когда времени уже нет',
                'tags': ['работа', 'офис', 'учеба']
            },
            {
                'title': 'Новый фреймворк',
                'description': 'Опять все меняется',
                'tags': ['программирование', 'IT', 'учеба']
            },
            {
                'title': 'Тестировщик нашел баг',
                'description': 'Снова работа для программиста',
                'tags': ['программирование', 'работа', 'юмор']
            }
        ]
        
        # 4. Создаем мемы
        created_count = 0
        for meme_data in test_memes:
            # Пропускаем если уже существует
            if Meme.objects.filter(title=meme_data['title']).exists():
                self.stdout.write(f"Пропуск: мем '{meme_data['title']}' уже существует")
                continue
            
            try:
                # Создаем мем
                meme = Meme.objects.create(
                    title=meme_data['title'],
                    description=meme_data['description'],
                    author=user,
                    is_published=True,
                    views_count=random.randint(50, 1000),
                    likes_count=random.randint(10, 500)
                )
                
                # Устанавливаем случайную дату
                days_ago = random.randint(0, 60)
                meme.created_at = datetime.now() - timedelta(days=days_ago)
                meme.save()
                
                # Добавляем теги
                for tag_name in meme_data['tags']:
                    if tag_name in tags_dict:
                        meme.tags.add(tags_dict[tag_name])
                
                created_count += 1
                self.stdout.write(f"✓ {meme_data['title']} - теги: {', '.join(meme_data['tags'])}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка: {meme_data['title']} - {e}"))
        
        # 5. Итоги
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"СОЗДАНО МЕМОВ: {created_count}"))
        self.stdout.write(f"Всего мемов в базе: {Meme.objects.count()}")
        self.stdout.write(f"Всего тегов в базе: {Tag.objects.count()}")
        
        # 6. Проверка
        self.stdout.write("\nПРОВЕРКА ТЕГОВ:")
        memes_without_tags = 0
        for meme in Meme.objects.all().prefetch_related('tags'):
            tags_count = meme.tags.count()
            if tags_count == 0:
                memes_without_tags += 1
                self.stdout.write(self.style.WARNING(f"⚠️  Без тегов: {meme.title}"))
        
        if memes_without_tags == 0:
            self.stdout.write(self.style.SUCCESS("✓ У всех мемов есть теги!"))
        else:
            self.stdout.write(self.style.ERROR(f"⚠️  Мемов без тегов: {memes_without_tags}"))