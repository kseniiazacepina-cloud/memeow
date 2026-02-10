from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Max, Q, F
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
import json
from datetime import datetime, timedelta
import random
from .utils import log_user_activity, track_like_activity, track_report_activity
from .models import Meme, Tag, Like, Favorite, Report, Notification, UserActivity
from .forms import MemeForm, TagForm
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import User

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
        moderation_status='approved',
        is_published=True
    )
    
    # Увеличиваем счетчик просмотров
    meme.views_count += 1
    meme.save(update_fields=['views_count'])
    
    # Логируем просмотр (если пользователь авторизован)
    if request.user.is_authenticated:
        log_user_activity(
            user=request.user,
            action_type='view_meme',
            description=f'Просмотр мема: {meme.title}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            meme=meme
        )
    
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
    
    # Используем get_or_create для атомарной операции
    like, created = Like.objects.get_or_create(user=request.user, meme=meme)
    
    if not created:
        # Удаляем лайк
        like.delete()
        meme.likes_count = max(0, meme.likes_count - 1)
        liked = False
        action = 'unlike'
    else:
        # Лайк создан
        meme.likes_count += 1
        liked = True
        action = 'like'
        
        # Отправляем уведомление автору мема (если это не сам автор)
        if meme.author != request.user:
            Notification.objects.create(
                user=meme.author,
                notification_type='meme_approved',
                title=f'Новый лайк от {request.user.username}',
                message=f'Пользователь {request.user.username} поставил лайк вашему мему "{meme.title}"',
                related_meme=meme
            )
    
    meme.save(update_fields=['likes_count'])
    
    # Логируем активность лайка
    track_like_activity(request.user, meme, action)
    
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
        
        # Логируем активность жалобы
        track_report_activity(request.user, meme)
        
        # Отправляем уведомление
        from .utils import send_report_notification
        send_report_notification(meme, request.user)
        
        messages.success(request, 'Жалоба отправлена.')
        return redirect('meme_detail', pk=pk)
    
    return render(request, 'memes/report_meme.html', {'meme': meme})

def is_staff_user(user):
    return user.is_staff

@user_passes_test(is_staff_user)
def report_management(request):
    """Страница управления жалобами для администраторов"""
    from django.db.models import Count
    
    # Активные жалобы (не рассмотренные)
    active_reports = Report.objects.filter(
        is_resolved=False
    ).select_related('meme', 'reporter', 'meme__author').order_by('-created_at')
    
    # Рассмотренные жалобы
    resolved_reports = Report.objects.filter(
        is_resolved=True
    ).select_related('meme', 'reporter', 'resolved_by').order_by('-resolved_at')[:50]
    
    # Статистика
    stats = {
        'total': Report.objects.count(),
        'active': active_reports.count(),
        'resolved': resolved_reports.count(),
    }
    
    context = {
        'active_reports': active_reports,
        'resolved_reports': resolved_reports,
        'stats': stats,
        'title': 'Управление жалобами',
    }
    
    return render(request, 'memes/report_management.html', context)

@user_passes_test(is_staff_user)
@require_POST
def resolve_report(request, report_id):
    """Рассмотреть жалобу"""
    report = get_object_or_404(Report, id=report_id)
    action = request.POST.get('action')
    resolution_notes = request.POST.get('resolution_notes', '')
    
    if action == 'delete_meme':
        # Удаляем мем
        meme_title = report.meme.title
        report.meme.delete()
        report.resolve(request.user, f"Мем удален: {resolution_notes}")
        messages.success(request, f'Мем "{meme_title}" удален.')
        
    elif action == 'dismiss_report':
        # Отклоняем жалобу
        report.resolve(request.user, f"Жалоба отклонена: {resolution_notes}")
        messages.success(request, 'Жалоба отклонена.')
        
    elif action == 'warn_user':
        # Предупреждаем автора
        report.meme.moderation_status = 'pending'
        report.meme.is_published = False
        report.meme.save()
        report.resolve(request.user, f"Автор предупрежден: {resolution_notes}")
        messages.success(request, 'Автор предупрежден.')
    
    return redirect('report_management')

@user_passes_test(is_staff_user)
@require_POST
def delete_report(request, report_id):
    """Удалить жалобу"""
    report = get_object_or_404(Report, id=report_id)
    report.delete()
    messages.success(request, 'Жалоба удалена.')
    return redirect('report_management')


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

@user_passes_test(lambda u: u.is_staff)
def user_activity_dashboard(request):
    """Дашборд активности пользователей"""
    
    # Периоды для статистики
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Основная статистика
    stats = {
        'total_users': User.objects.count(),
        'active_today': UserActivity.objects.filter(
            created_at__date=today
        ).values('user').distinct().count(),
        'active_week': UserActivity.objects.filter(
            created_at__date__gte=week_ago
        ).values('user').distinct().count(),
        'total_activities': UserActivity.objects.count(),
        'activities_today': UserActivity.objects.filter(created_at__date=today).count(),
        'activities_week': UserActivity.objects.filter(created_at__date__gte=week_ago).count(),
    }
    
    # Топ активных пользователей
    top_users = UserActivity.objects.filter(
        created_at__date__gte=week_ago
    ).values(
        'user__username', 'user__id'
    ).annotate(
        activity_count=Count('id'),
        last_activity=Max('created_at')  # Используем Max напрямую
    ).order_by('-activity_count')[:20]
    
    # Статистика по действиям
    activity_by_type = UserActivity.objects.filter(
        created_at__date__gte=week_ago
    ).values('action_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Последние активности
    recent_activities = UserActivity.objects.select_related(
        'user', 'meme'
    ).order_by('-created_at')[:50]
    
    # Популярные мемы (по просмотрам)
    popular_memes = UserActivity.objects.filter(
        action_type='view_meme',
        created_at__date__gte=week_ago
    ).values(
        'meme__title', 'meme__id'
    ).annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:10]
    
    # Активность по часам (за сегодня)
    today_activities = UserActivity.objects.filter(
        created_at__date=today
    ).extra({
        'hour': "EXTRACT(HOUR FROM created_at)"
    }).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    context = {
        'stats': stats,
        'top_users': top_users,
        'activity_by_type': activity_by_type,
        'recent_activities': recent_activities,
        'popular_memes': popular_memes,
        'today_activities': today_activities,
        'today': today,
        'week_ago': week_ago,
        'title': 'Дашборд активности пользователей',
    }
    
    return render(request, 'memes/activity_dashboard.html', context)

@user_passes_test(lambda u: u.is_staff)
def user_activity_detail(request, user_id):
    """Детальная статистика активности конкретного пользователя"""
    user = get_object_or_404(User, id=user_id)
    
    # Периоды для статистики
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Получаем всю активность пользователя
    activities = UserActivity.objects.filter(user=user).select_related('meme').order_by('-created_at')
    
    # Статистика по периодам
    stats = {
        'total': activities.count(),
        'today': activities.filter(created_at__date=today).count(),
        'week': activities.filter(created_at__date__gte=week_ago).count(),
        'month': activities.filter(created_at__date__gte=month_ago).count(),
    }
    
    # Статистика по типам действий
    activity_by_type = activities.values('action_type').annotate(
        count=Count('id'),
        last_activity=Max('created_at')
    ).order_by('-count')
    
    # Последние активности
    recent_activities = activities[:50]
    
    # Популярные мемы (которые пользователь просматривал/лайкал)
    popular_memes = activities.filter(
        meme__isnull=False
    ).values(
        'meme__title', 'meme__id'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Активность по дням (за последние 30 дней)
    activity_by_day = activities.filter(
        created_at__date__gte=month_ago
    ).extra({
        'day': "DATE(created_at)"
    }).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    context = {
        'user': user,
        'stats': stats,
        'activity_by_type': activity_by_type,
        'recent_activities': recent_activities,
        'popular_memes': popular_memes,
        'activity_by_day': activity_by_day,
        'today': today,
        'week_ago': week_ago,
        'month_ago': month_ago,
        'title': f'Активность пользователя {user.username}',
    }
    
    return render(request, 'memes/user_activity_detail.html', context)