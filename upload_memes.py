import os
import sys
import random

for module in list(sys.modules.keys()):
    if 'django' in module or 'users' in module or 'memes' in module:
        del sys.modules[module]

project_path = os.path.normpath('C:/Users/User/Documents/GitHub/memeow')
sys.path.insert(0, project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memeow_project.settings')

print(f"Путь: {project_path}")

try:
    import django
    django.setup()
    print("✓ Django настроен успешно!")
except Exception as e:
    print(f"✗ Ошибка: {e}")
    sys.exit(1)


from pathlib import Path
from django.core.files import File
from django.contrib.auth.models import User
from memes.models import Meme, Tag  
from django.utils.text import slugify
from django.utils import timezone
print("✓ Модели импортированы")

MEMES_DATA = [
    {
        'filename': 'understand_nothing.jpg',
        'title': 'котик ничего не понял',
        'description': 'хорошо, что вы мне всё объяснили. плохо, что я ничего не понял',
        'tag': ['Коты', 'Смешные', 'Животные']
    },
    {
        'filename': 'late.jpg', 
        'title': 'я опоздаю',
        'description': 'в связи с предвиденными обстоятельствами, которые я прекрасно могу контролировать, я опоздаю',
        'tag': ['Смешные', 'Животные', 'Капибара', 'Опоздание']
    },
    {
        'filename': 'important_matter.jpg',
        'title': 'важные дела',
        'description': 'я и важные дела, на которые я забил',
        'tag': ['Мемы', 'Смешные', 'Работа', 'Лень']
    },
    {
        'filename': 'pupupu.jpg',
        'title': 'пу-пу-пу...',
        'description': 'нет слов, пу-пу-пу...',
        'tag': ['Смешные', 'Животные', 'Крыса']
    },
    {
        'filename': 'comfort_zone.jpg',
        'title': 'зона комфорта',
        'description': 'выйди из зоны комфорта, хватит деградировать',
        'tag': ['Коты', 'Смешные', 'Животные' 'Деградация', 'Комфорт', 'Лень']
    },
    {
        'filename': 'sarcasm.jpg',
        'title': 'сарказм',
        'description': 'животное, полное сарказма',
        'tag': ['Другое', 'Сарказм', 'Смешные']
    },
]

#категории, которые должны быть созданы всегда
REQUIRED_TAGS = [
    'Смешные', 'Мемы', 'Юмор', 'Коты',
    'IT', 'Работа', 'Животные', 'Интернет'
]

def get_or_create_tag(name):
    """Создает или получает тег по имени"""
    slug = slugify(name)
    tag, created = Tag.objects.get_or_create(
        name=name,
        defaults={'slug': slug}
    )
    return tag

def upload_memes_with_tags():
    """
    Загружает мемы на сайт из папки static/images/memes/
    Использует теги (Tags) вместо категорий
    """
    
    print("ЗАГРУЗКА МЕМОВ С ТЕГАМИ")
    
    #получаем пользователя
    user, user_created = User.objects.get_or_create(
        username='хтонь',
        defaults={
            'email': 'chtonic@memeow.com',
            'first_name': 'хтонь',
            'last_name': 'мастер мемов',
            'is_active': True
        }
    )

    if user_created:
        user.set_password('memaster123')
        user.save()
        print(f"Создан пользователь: {user.username}")
    else:
        print(f"Используем существующего пользователя: {user.username}")
    
    #путь к изображениям
    base_dir = Path(__file__).parent
    images_dir = base_dir / 'static' / 'images' / 'memes'
    
    print(f"Ищем изображения в: {images_dir}\n")
    
    if not images_dir.exists():
        print(f"Папка не найдена!")
        print(f"Создаю папку...")
        images_dir.mkdir(parents=True, exist_ok=True)
        print(f"Папка создана: {images_dir}")
        print(f"\nПоместите в нее изображения:")
        for meme in MEMES_DATA:
            print(f"   - {meme['filename']}")
        return
    
    #проверяем существование файлов
    existing_files = []
    missing_files = []
    
    for meme in MEMES_DATA:
        file_path = images_dir / meme['filename']
        if file_path.exists():
            existing_files.append(meme['filename'])
        else:
            missing_files.append(meme['filename'])
    
    print(f"Найдено файлов: {len(existing_files)}")
    if missing_files:
        print(f"Отсутствуют файлы: {len(missing_files)}")
        for filename in missing_files:
            print(f"   - {filename}")
    
    if not existing_files:
        print("\nНет файлов для загрузки!")
        return
    
    #загружаем мемы
    successful = 0
    skipped = 0
    errors = 0
    
    print("Процесс загрузки:")
    
    for i, meme_info in enumerate(MEMES_DATA, 1):
        filename = meme_info['filename']
        title = meme_info['title']
        description = meme_info.get('description', '')
        tag_names = meme_info.get('tags', [])
        
        print(f"\n{i}.Загружаем: '{title}'")
        print(f"Файл: {filename}")
        
        #проверяем существование файла
        file_path = images_dir / filename
        if not file_path.exists():
            print(f"Файл не найден, пропускаем")
            errors += 1
            continue
        
        #проверяем, не существует ли уже мем с таким названием
        if Meme.objects.filter(title=title).exists():
            print(f"Мем уже существует, пропускаем")
            skipped += 1
            continue
        
        try:
            #создаем мем
            meme = Meme.objects.create(
                title=title,
                description=description,
                author=user,
                likes_count=random.randint(15, 250),
                views_count=random.randint(50, 1500),
                is_published=True,
                created_at=timezone.now(),
            )
            
            #загружаем изображение
            with open(file_path, 'rb') as f:
                meme.image.save(filename, File(f), save=True)
            
            #создаем и добавляем теги
            tag_objects = []
            for tag_name in tag_names:
                tag = get_or_create_tag(tag_name)
                tag_objects.append(tag)
            
            if tag_objects:
                meme.tags.set(tag_objects)
            
            successful += 1
            print(f"Успешно загружен!")
            print(f"{description[:80]}..." if len(description) > 80 else f"{description}")
            print(f"Теги: {', '.join(tag_names)}")
            print(f"Лайки: {meme.likes_count}")
            print(f"Просмотры: {meme.views_count}")
            
        except Exception as e:
            print(f"Ошибка: {str(e)}")
            errors += 1
    
    #результаты
    print("Результаты загрузки:")
    print(f"Успешно загружено: {successful}")
    print(f"Пропущено (уже есть): {skipped}")
    print(f"Ошибок/не найдено: {errors}")
    print(f"Всего в списке: {len(MEMES_DATA)}")
    
    #статистика по тегам
    if successful > 0:
        print(f"\nСОЗДАННЫЕ ТЕГИ:")
        all_tags = set()
        for meme in MEMES_DATA:
            all_tags.update(meme.get('tags', []))
        
        for tag_name in sorted(all_tags):
            tag_count = Tag.objects.filter(name=tag_name).count()
            print(f"   - {tag_name}")
        
        print(f"\nГотово! Все мемы успешно загружены на сайт!")

def main():
    """Главная функция"""
    try:
        upload_memes_with_tags()
    except KeyboardInterrupt:
        print("\n\nЗагрузка прервана пользователем")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()