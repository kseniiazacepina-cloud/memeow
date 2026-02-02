from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Count
from memes.models import Meme, Favorite

from .forms import UserUpdateForm, ProfileUpdateForm

@login_required
def profile(request, username=None):
    """Страница профиля пользователя"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    # Статистика пользователя
    user_memes = Meme.objects.filter(author=user, is_published=True)
    user_favorites = Favorite.objects.filter(user=user).select_related('meme')
    
    # Популярные теги пользователя
    from memes.models import Tag
    user_tags = Tag.objects.filter(
        memes__author=user
    ).annotate(
        meme_count=Count('memes')
    ).order_by('-meme_count')[:10]
    
    context = {
        'profile_user': user,
        'user_memes': user_memes[:6],  # Последние 6 мемов
        'user_favorites': [fav.meme for fav in user_favorites[:6]],
        'memes_count': user_memes.count(),
        'likes_received': sum(meme.likes_count for meme in user_memes),
        'user_tags': user_tags,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def favorites(request):
    """Страница избранного пользователя"""
    pass

@login_required
def settings_view(request):
    """Настройки профиля пользователя"""
    pass

@login_required
def dashboard(request):
    """Панель управления пользователя"""
    pass

class ProfileDetailView(DetailView):
    """Детальное представление профиля (для API-like view)"""
    pass

