from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
import json
from datetime import datetime, timedelta
import random

from .models import Meme, Tag, Like, Favorite
from .forms import MemeForm, TagForm
from users.models import Profile

def home(request):
    """Главная страница"""
    # Популярные теги
    popular_tags = Tag.objects.annotate(
        meme_count=Count('memes')
    ).order_by('-meme_count')[:20]
    
    # Последние мемы
    latest_memes = Meme.objects.filter(
        is_published=True
    ).select_related('author').prefetch_related('tags').order_by('-created_at')[:12]
    
    # Мем дня (упрощенная версия)
    meme_of_the_day = get_meme_of_the_day()
    
    context = {
        'latest_memes': latest_memes,
        'popular_tags': popular_tags,
        'meme_of_the_day': meme_of_the_day,
        'total_memes': Meme.objects.filter(is_published=True).count(),
        'total_users': Profile.objects.count(),
    }
    
    return render(request, 'memes/home.html', context)

def meme_detail(request, pk):
    """Детальная страница мема"""
    meme = get_object_or_404(
        Meme.objects.select_related('author').prefetch_related('tags'),
        pk=pk,
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
    if request.method == 'POST':
        form = MemeForm(request.POST, request.FILES)
        if form.is_valid():
            meme = form.save(commit=False)
            meme.author = request.user
            meme.save()
            form.save_m2m()  # Сохраняем ManyToMany поле (теги)
            
            messages.success(request, 'Мем успешно добавлен! Он появится после модерации.')
            return redirect('meme_detail', pk=meme.pk)
    else:
        form = MemeForm()
    
    # Все теги для автодополнения
    all_tags = Tag.objects.all()
    
    context = {
        'form': form,
        'all_tags': all_tags,
    }
    
    return render(request, 'memes/add_meme.html', context)

@login_required
def edit_meme(request, pk):
    """Редактирование мема"""
    meme = get_object_or_404(Meme, pk=pk)
    
    # Проверяем, что пользователь - автор мема
    if meme.author != request.user and not request.user.is_staff:
        messages.error(request, 'Вы не можете редактировать этот мем.')
        return redirect('meme_detail', pk=pk)
    
    if request.method == 'POST':
        form = MemeForm(request.POST, request.FILES, instance=meme)
        if form.is_valid():
            form.save()
            messages.success(request, 'Мем успешно обновлен!')
            return redirect('meme_detail', pk=meme.pk)
    else:
        form = MemeForm(instance=meme)
    
    context = {
        'form': form,
        'meme': meme,
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
    tag = get_object_or_404(Tag, slug=slug)
    
    memes = Meme.objects.filter(
        tags=tag,
        is_published=True
    ).select_related('author').prefetch_related('tags').order_by('-created_at')
    
    # Пагинация
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
def toggle_like(request, pk):
    """Поставить/убрать лайк (AJAX)"""
    if request.method == 'POST' and request.is_ajax():
        meme = get_object_or_404(Meme, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user, meme=meme)
        
        if not created:
            like.delete()
            meme.likes_count -= 1
            liked = False
        else:
            meme.likes_count += 1
            liked = True
        
        meme.save(update_fields=['likes_count'])
        
        return JsonResponse({
            'liked': liked,
            'likes_count': meme.likes_count
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def toggle_favorite(request, pk):
    """Добавить/удалить из избранного (AJAX)"""
    if request.method == 'POST' and request.is_ajax():
        meme = get_object_or_404(Meme, pk=pk)
        favorite, created = Favorite.objects.get_or_create(user=request.user, meme=meme)
        
        if not created:
            favorite.delete()
            favorited = False
        else:
            favorited = True
        
        return JsonResponse({
            'favorited': favorited
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

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