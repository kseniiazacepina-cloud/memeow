import os
import sys
import django

# Добавляем корневую директорию проекта в Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Указываем правильный путь к настройкам
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memyau_project.settings')
django.setup()

from memes.models import Meme
from django.db.models import Q

def main():
    print("=" * 50)
    print("ПОИСК И УДАЛЕНИЕ МЕМОВ БЕЗ ИЗОБРАЖЕНИЙ")
    print("=" * 50)
    
    # Находим мемы без изображений
    memes_without_images = Meme.objects.filter(
        Q(image__isnull=True) | Q(image='')
    )
    
    count = memes_without_images.count()
    print(f"Найдено мемов без изображений: {count}")
    
    if count > 0:
        print("\nСписок мемов для удаления:")
        for meme in memes_without_images:
            print(f"  - ID {meme.id}: '{meme.title}'")
        
        # Подтверждение
        confirm = input(f"\nУдалить {count} мемов без изображений? (y/N): ")
        
        if confirm.lower() == 'y':
            deleted_count, _ = memes_without_images.delete()
            print(f"✅ Удалено мемов: {deleted_count}")
        else:
            print("❌ Удаление отменено")
    else:
        print("✅ Нет мемов без изображений")

if __name__ == '__main__':
    main()