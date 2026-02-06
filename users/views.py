from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Count, Sum
from memes.models import Meme, Favorite


from .forms import UserUpdateForm, ProfileUpdateForm, UserRegisterForm

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
    favorites = Favorite.objects.filter(user=request.user).select_related('meme')
    memes = [fav.meme for fav in favorites]
    
    context = {
        'favorite_memes': memes,
        'favorites_count': favorites.count(),
    }
    
    return render(request, 'users/favorites.html', context)

@login_required
def settings_view(request):
    """Настройки профиля пользователя"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'users/settings.html', context)

@login_required
def dashboard(request):
    """Панель управления пользователя"""
    # Последние действия
    recent_memes = Meme.objects.filter(author=request.user).order_by('-created_at')[:5]
    recent_favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('meme').order_by('-created_at')[:5]
    
    # Статистика
    total_memes = Meme.objects.filter(author=request.user).count()
    total_likes_received = Meme.objects.filter(
        author=request.user
    ).aggregate(total_likes=Sum('likes_count'))['total_likes'] or 0
    
    context = {
        'recent_memes': recent_memes,
        'recent_favorites': recent_favorites,
        'total_memes': total_memes,
        'total_likes_received': total_likes_received,
    }
    
    return render(request, 'users/dashboard.html', context)

class ProfileDetailView(DetailView):
    """Детальное представление профиля (для API-like view)"""
    model = User
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile_user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Получаем мемы пользователя
        context['memes'] = Meme.objects.filter(
            author=user, 
            is_published=True
        ).order_by('-created_at')[:12]
        
        # Статистика
        context['stats'] = {
            'memes_count': Meme.objects.filter(author=user).count(),
            'total_likes': sum(m.likes_count for m in context['memes']),
            'joined_date': user.date_joined.strftime('%d.%m.%Y'),
        }
        
        return context

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})