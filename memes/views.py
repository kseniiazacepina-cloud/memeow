from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
import json
from datetime import datetime, timedelta
import random
from .models import Meme, Tag, Like, Favorite, Report, Notification
from .forms import MemeForm, TagForm
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

def home(request):
    """Главная страница"""
    # Только одобренные мемы
    published_memes = Meme.objects.filter(
        moderation_status='approved',
        is_published=True
    )
    
    try:
        # 1. Мем дня (стабильный на весь день)
        today = datetime.now().date()
        seed = today.year * 10000 + today.month * 100 + today.day
        random.seed(seed)
        
        all_memes = Meme.objects.filter(is_published=True)
        meme_of_the_day = random.choice(list(all_memes)) if all_memes else None
    except Exception as e:
        meme_of_the_day = None
        print(f"Ошибка при выборе мема дня: {e}")
    
    try:
        # 2. Свежие мемы (последние 12)
        recent_memes = Meme.objects.filter(
            is_published=True
        ).select_related('author').prefetch_related('tags').order_by('-created_at')[:12]
    except Exception as e:
        recent_memes = []
        print(f"Ошибка при загрузке свежих мемов: {e}")
    
    try:
        # 3. Популярные мемы (по лайкам)
        popular_memes = Meme.objects.filter(is_published=True).order_by('-likes_count', '-created_at')[:6]
    except Exception as e:
        popular_memes = []
    
    try:
        # 4. Популярные теги
        popular_tags = Tag.objects.annotate(
            meme_count=Count('memes')
        ).order_by('-meme_count')[:10]
    except Exception as e:
        popular_tags = []

     # Сбрасываем seed для других случайных операций
    random.seed()   
    
    context = {
        'meme_of_the_day': meme_of_the_day,
        'recent_memes': recent_memes,
        'popular_memes': popular_memes,
        'popular_tags': popular_tags,
    }
    
    return render(request, 'memes/home.html', context)

def meme_detail(request, pk):
    """Детальная страница мема"""
    meme = get_object_or_404(
        Meme.objects.select_related('author').prefetch_related('tags'),
        pk=pk,
        moderation_status='approved',  # ← Добавьте это
        is_published=True
    )
    
    # Увеличиваем счетчик просмотров
    meme.views_count += 1
    meme.save(update_fields=['views_count'])
    
    # Похожие мемы (по тегам)
    similar_memes = Meme.objects.filter(
        tags__in=meme.tags.all(),
        is_published=True
    ).exclude(id=meme.id).distinct()[:6]
    
    # Проверяем, лайкнул ли пользователь этот мем
    is_liked = False
    is_favorite = False
    if request.user.is_authenticated:
        is_liked = Like.objects.filter(user=request.user, meme=meme).exists()
        is_favorite = Favorite.objects.filter(user=request.user, meme=meme).exists()
    
    context = {
        'meme': meme,
        'similar_memes': similar_memes,
        'is_liked': is_liked,
        'is_favorite': is_favorite,
    }
    
    return render(request, 'memes/meme_detail.html', context)

@login_required
def add_meme(request):
    """Добавление нового мема"""
    all_tags = Tag.objects.all()
    
    if request.method == 'POST':
        form = MemeForm(request.POST, request.FILES)
        if form.is_valid():
            meme = form.save(commit=False)
            meme.author = request.user
            meme.moderation_status = 'pending'  # На рассмотрении
            meme.is_published = False  # Не публикуем до одобрения
            meme.save()
            form.save_m2m()
            
            messages.success(request, 'Мем успешно добавлен и отправлен на модерацию!')
            return redirect('my_memes')
    else:
        form = MemeForm()
    
    context = {
        'form': form,
        'all_tags': all_tags,
    }
    
    return render(request, 'memes/add_meme.html', context)

@login_required
def my_memes(request):
    """Страница с мемами пользователя"""
    memes = Meme.objects.filter(author=request.user).order_by('-created_at')
    
    # Разделяем по статусам
    pending_memes = memes.filter(moderation_status='pending')
    approved_memes = memes.filter(moderation_status='approved')
    rejected_memes = memes.filter(moderation_status='rejected')
    
    context = {
        'memes': memes,
        'pending_memes': pending_memes,
        'approved_memes': approved_memes,
        'rejected_memes': rejected_memes,
        'total_memes': memes.count(),
        'pending_count': pending_memes.count(),
        'approved_count': approved_memes.count(),
        'rejected_count': rejected_memes.count(),
        'title': 'Мои мемы',
    }
    
    return render(request, 'memes/my_memes.html', context)

@login_required
def edit_meme(request, pk):
    """Редактирование мема"""
    meme = get_object_or_404(Meme, pk=pk)
    all_tags = Tag.objects.all()  # Получаем все теги
    
    # Проверяем, что пользователь - автор мема
    if meme.author != request.user and not request.user.is_staff:
        messages.error(request, 'Вы не можете редактировать этот мем.')
        return redirect('meme_detail', pk=pk)
    
    if request.method == 'POST':
        form = MemeForm(request.POST, request.FILES, instance=meme)
        if form.is_valid():
            meme = form.save()
            messages.success(request, 'Мем успешно обновлен!')
            return redirect('meme_detail', pk=meme.pk)
    else:
        form = MemeForm(instance=meme)
    
    context = {
        'form': form,
        'meme': meme,
        'all_tags': all_tags,  # Передаем теги в шаблон
    }
    
    return render(request, 'memes/edit_meme.html', context)

@login_required
def delete_meme(request, pk):
    """Удаление мема"""
    meme = get_object_or_404(Meme, pk=pk)
    
    if meme.author != request.user and not request.user.is_staff:
        messages.error(request, 'Вы не можете удалить этот мем.')
        return redirect('meme_detail', pk=pk)
    
    if request.method == 'POST':
        meme.delete()
        messages.success(request, 'Мем успешно удален!')
        return redirect('home')
    
    return render(request, 'memes/delete_meme.html', {'meme': meme})

def tag_memes(request, slug):
    """Мемы по тегу"""
    # Находим тег по slug
    tag = get_object_or_404(Tag, slug=slug)
    
    memes = Meme.objects.filter(
        tags=tag,
        is_published=True
    ).select_related('author').prefetch_related('tags').order_by('-created_at')
    
    # Пагинация
    from django.core.paginator import Paginator
    paginator = Paginator(memes, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'memes': page_obj,
        'memes_count': memes.count(),
    }
    
    return render(request, 'memes/tag_list.html', context)

def search(request):
    """Поиск мемов"""
    query = request.GET.get('q', '')
    
    if query:
        memes = Meme.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query),
            is_published=True
        ).select_related('author').prefetch_related('tags').distinct().order_by('-created_at')
    else:
        memes = Meme.objects.none()
    
    # Пагинация
    paginator = Paginator(memes, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'memes': page_obj,
        'memes_count': memes.count(),
    }
    
    return render(request, 'memes/search_results.html', context)

@login_required
@require_POST
@csrf_exempt
def toggle_like(request, pk):
    """Поставить/убрать лайк (AJAX)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Необходимо авторизоваться'}, status=403)
    
    meme = get_object_or_404(Meme, pk=pk)
    
    # Проверяем, не лайкал ли уже пользователь
    like_exists = Like.objects.filter(user=request.user, meme=meme).exists()
    
    if like_exists:
        # Удаляем лайк
        Like.objects.filter(user=request.user, meme=meme).delete()
        meme.likes_count = max(0, meme.likes_count - 1)
        liked = False
    else:
        # Добавляем лайк
        Like.objects.create(user=request.user, meme=meme)
        meme.likes_count += 1
        liked = True
        
        # Отправляем уведомление автору мема (если это не сам автор)
        if meme.author != request.user:
            Notification.objects.create(
                user=meme.author,
                notification_type='meme_approved',  # Используем существующий тип
                title=f'Новый лайк от {request.user.username}',
                message=f'Пользователь {request.user.username} поставил лайк вашему мему "{meme.title}"',
                related_meme=meme
            )
    
    meme.save(update_fields=['likes_count'])
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': meme.likes_count
    })

@login_required
@require_POST
@csrf_exempt
def toggle_favorite(request, pk):
    """Добавить/удалить из избранного (AJAX)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Необходимо авторизоваться'}, status=403)
    
    meme = get_object_or_404(Meme, pk=pk)
    
    # Проверяем, не в избранном ли уже
    favorite_exists = Favorite.objects.filter(user=request.user, meme=meme).exists()
    
    if favorite_exists:
        # Удаляем из избранного
        Favorite.objects.filter(user=request.user, meme=meme).delete()
        favorited = False
    else:
        # Добавляем в избранное
        Favorite.objects.create(user=request.user, meme=meme)
        favorited = True
        
        # Отправляем уведомление автору мема (если это не сам автор)
        if meme.author != request.user:
            Notification.objects.create(
                user=meme.author,
                notification_type='meme_reported',  # Используем другой существующий тип
                title=f'Мем добавлен в избранное',
                message=f'Пользователь {request.user.username} добавил ваш мем "{meme.title}" в избранное',
                related_meme=meme
            )
    
    return JsonResponse({
        'success': True,
        'favorited': favorited
    })

@login_required
def notifications(request):
    """Уведомления пользователя"""
    # Получаем все уведомления
    notifications_list = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Считаем только непрочитанные уведомления
    unread_count = notifications_list.filter(is_read=False).count()
    
    # Пагинация
    paginator = Paginator(notifications_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'unread_count': unread_count,
        'title': 'Уведомления',
    }
    
    return render(request, 'memes/notifications.html', context)

@login_required
@require_POST
def mark_notification_read(request, pk):
    """Пометить одно уведомление как прочитанное"""
    try:
        notification = Notification.objects.get(id=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Уведомление не найдено'}, status=404)

@login_required
@require_POST
def mark_all_notifications_read(request):
    """Пометить все уведомления как прочитанные"""
    try:
        updated = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(is_read=True)
        return JsonResponse({'success': True, 'updated': updated})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def delete_notification(request, pk):
    """Удалить одно уведомление"""
    try:
        notification = Notification.objects.get(id=pk, user=request.user)
        notification.delete()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Уведомление не найдено'}, status=404)

@login_required
@require_POST
def delete_all_notifications(request):
    """Удалить все уведомления пользователя"""
    try:
        deleted = Notification.objects.filter(user=request.user).delete()
        return JsonResponse({'success': True, 'deleted': deleted[0]})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def get_meme_of_the_day():
    """Получить мем дня (упрощенная версия)"""
    # Используем дату как seed для рандома, чтобы мем дня менялся раз в день
    today = datetime.now().date()
    seed = today.year * 10000 + today.month * 100 + today.day
    
    # Получаем все опубликованные мемы
    memes = Meme.objects.filter(is_published=True)
    
    if memes.exists():
        # Используем seed для выбора одного и того же мема в течение дня
        random.seed(seed)
        return random.choice(list(memes))
    
    return None

def random_meme(request):
    """Случайный мем"""
    memes = Meme.objects.filter(is_published=True)
    
    if memes.exists():
        random_meme = random.choice(list(memes))
        return redirect('meme_detail', pk=random_meme.pk)
    
    messages.info(request, 'Пока нет мемов.')
    return redirect('home')

def popular_memes(request):
    """Популярные мемы (по лайкам)"""
    memes = Meme.objects.filter(
        is_published=True
    ).select_related('author').prefetch_related('tags').order_by('-likes_count', '-created_at')
    
    # Пагинация
    paginator = Paginator(memes, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'memes': page_obj,
        'title': 'Популярные мемы',
    }
    
    return render(request, 'memes/meme_list.html', context)

def download_meme(request, pk):
    """Скачать мем"""
    meme = get_object_or_404(Meme, pk=pk, is_published=True)
    
    response = HttpResponse(meme.image.read(), content_type='image/jpeg')
    response['Content-Disposition'] = f'attachment; filename="{meme.title}.jpg"'
    return response

def meme_list(request):
    """Список всех мемов"""
    memes = Meme.objects.filter(is_published=True).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(memes, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'memes': page_obj,
        'title': 'Все мемы',
    }
    
    return render(request, 'memes/meme_list.html', context)

@login_required
def report_meme(request, pk):
    """Пожаловаться на мем"""
    meme = get_object_or_404(Meme, pk=pk, is_published=True)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')
        
        if not reason:
            messages.error(request, 'Выберите причину жалобы.')
            return redirect('meme_detail', pk=pk)
        
        # Создаем жалобу
        report = Report.objects.create(
            meme=meme,
            reporter=request.user,
            reason=reason,
            description=description
        )
        
        # Отправляем уведомление автору
        from .utils import send_report_notification
        send_report_notification(meme, request.user)
        
        messages.success(request, 'Жалоба отправлена. Спасибо за бдительность!')
        return redirect('meme_detail', pk=pk)
    
    return render(request, 'memes/report_meme.html', {'meme': meme})

@login_required
def report_meme(request, pk):
    """Пожаловаться на мем"""
    meme = get_object_or_404(Meme, pk=pk, is_published=True)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')
        
        if not reason:
            messages.error(request, 'Выберите причину жалобы.')
            return redirect('meme_detail', pk=pk)
        
        # Создаем жалобу
        report = Report.objects.create(
            meme=meme,
            reporter=request.user,
            reason=reason,
            description=description
        )
        
        # Отправляем уведомление автору
        from .utils import send_report_notification
        send_report_notification(meme, request.user)
        
        messages.success(request, 'Жалоба отправлена. Спасибо за бдительность!')
        return redirect('meme_detail', pk=pk)
    
    return render(request, 'memes/report_meme.html', {'meme': meme})


@staff_member_required
@permission_required('memes.can_moderate', raise_exception=True)
def moderation_queue(request):
    """
    Представление для отображения очереди модерации мемов
    """
    # Получаем мемы, ожидающие модерации
    pending_memes = Meme.objects.filter(
        moderation_status='pending',
        is_published=False
    ).order_by('created_at')
    
    # Получаем недавно одобренные/отклоненные мемы
    recent_moderated = Meme.objects.filter(
        moderation_status__in=['approved', 'rejected']
    ).order_by('-moderated_at')[:10]
    
    # Статистика для шаблона
    total_memes = Meme.objects.count()
    published_memes = Meme.objects.filter(is_published=True).count()
    rejected_memes = Meme.objects.filter(moderation_status='rejected').count()
    
    context = {
        'pending_memes': pending_memes,
        'recent_moderated': recent_moderated,
        'total_memes': total_memes,
        'published_memes': published_memes,
        'rejected_memes': rejected_memes,
        'title': 'Очередь модерации',
    }
    
    return render(request, 'memes/moderation_queue.html', context)