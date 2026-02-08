import os
import django
import sys

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memyau_project.settings')
django.setup()

from django.contrib.auth.models import User
from memes.models import Meme, Tag
from django.core.files import File
from datetime import datetime, timedelta
import random

def upload_test_memes():
    """Загрузка тестовых мемов с тегами"""
    print("=" * 50)
    print("НАЧАЛО ЗАГРУЗКИ ТЕСТОВЫХ МЕМОВ")
    print("=" * 50)
    
    # 1. Получаем или создаем тестового пользователя
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_active': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Создан пользователь: {user.username}")
    else:
        print(f"✓ Используем существующего пользователя: {user.username}")
    
    # 2. Создаем базовые теги если их нет
    base_tags = [
        'котики', 'собаки', 'животные', 'юмор', 'мемы',
        'программирование', 'IT', 'работа', 'офис', 'учеба',
        'игры', 'кино', 'фильмы', 'музыка', 'спорт'
    ]
    
    tags_dict = {}
    for tag_name in base_tags:
        from django.utils.text import slugify
        slug = slugify(tag_name, allow_unicode=True)
        
        tag, created = Tag.objects.get_or_create(
            slug=slug,
            defaults={'name': tag_name}
        )
        
        if created:
            print(f"✓ Создан тег: {tag_name}")
        else:
            # Обновляем имя если нужно
            if tag.name != tag_name:
                tag.name = tag_name
                tag.save()
                print(f"✓ Обновлен тег: {tag_name}")
        
        tags_dict[tag_name] = tag
    
    print(f"✓ Всего тегов: {len(tags_dict)}")
    
    # 3. Тестовые мемы (без реальных изображений)
    test_memes = [
        {
            'title': 'Когда код работает с первого раза',
            'description': 'Редкое, но очень приятное чувство',
            'tags': ['программирование', 'IT', 'юмор']
        },
        {
            'title': 'Понедельник у программиста',
            'description': 'Хочу обратно в выходные',
            'tags': ['работа', 'офис', 'юмор']
        },
        {
            'title': 'Мой код vs Код коллеги',
            'description': 'Всегда кажется, что чужой код лучше',
            'tags': ['программирование', 'работа', 'юмор']
        },
        {
            'title': 'Когда находишь баг в продакшене',
            'description': 'Паника и поиск костылей',
            'tags': ['программирование', 'IT', 'работа']
        },
        {
            'title': 'Милый котик программист',
            'description': 'Котик тоже умеет писать код',
            'tags': ['котики', 'программирование', 'юмор']
        },
        {
            'title': 'Собака-тестировщик',
            'description': 'Нашел все баги в проекте',
            'tags': ['собаки', 'программирование', 'юмор']
        },
        {
            'title': 'Работа из дома',
            'description': 'Пижама и кофе - лучшая форма одежды',
            'tags': ['работа', 'офис', 'юмор']
        },
        {
            'title': 'Дедлайн через час',
            'description': 'Адреналин и паника одновременно',
            'tags': ['работа', 'учеба', 'юмор']
        },
        {
            'title': 'Оптимизация производительности',
            'description': 'Из 2 секунд сделали 1.9 секунд',
            'tags': ['программирование', 'IT', 'работа']
        },
        {
            'title': 'Новый фреймворк вышел',
            'description': 'Опять учиться заново',
            'tags': ['программирование', 'IT', 'учеба']
        }
    ]
    
    # 4. Создаем мемы
    created_count = 0
    for i, meme_data in enumerate(test_memes):
        # Проверяем, нет ли уже такого мема
        if Meme.objects.filter(title=meme_data['title']).exists():
            print(f"↻ Мем уже существует: {meme_data['title']}")
            continue
        
        # Создаем мем
        try:
            meme = Meme.objects.create(
                title=meme_data['title'],
                description=meme_data['description'],
                author=user,
                is_published=True,
                views_count=random.randint(10, 1000),
                likes_count=random.randint(5, 500)
            )
            
            # Устанавливаем случайную дату (в пределах последних 30 дней)
            days_ago = random.randint(0, 30)
            meme.created_at = datetime.now() - timedelta(days=days_ago)
            meme.save()
            
            # Добавляем теги
            tag_names = meme_data['tags']
            for tag_name in tag_names:
                if tag_name in tags_dict:
                    meme.tags.add(tags_dict[tag_name])
            
            created_count += 1
            print(f"✓ Создан мем: {meme_data['title']}")
            print(f"  Теги: {', '.join(tag_names)}")
            
        except Exception as e:
            print(f"✗ Ошибка при создании мема '{meme_data['title']}': {e}")
    
    print("\n" + "=" * 50)
    print("ИТОГИ ЗАГРУЗКИ")
    print("=" * 50)
    print(f"Создано мемов: {created_count}")
    print(f"Всего мемов в базе: {Meme.objects.count()}")
    print(f"Всего тегов в базе: {Tag.objects.count()}")
    
    # 5. Проверяем связи
    print("\n" + "=" * 50)
    print("ПРОВЕРКА СВЯЗЕЙ")
    print("=" * 50)
    
    for meme in Meme.objects.all().prefetch_related('tags'):
        tags = list(meme.tags.all())
        if tags:
            tag_names = [t.name for t in tags]
            print(f"Мем: '{meme.title}' - Теги: {', '.join(tag_names)}")
        else:
            print(f"Мем: '{meme.title}' - БЕЗ ТЕГОВ ⚠️")

if __name__ == '__main__':
    upload_test_memes()