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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import MemeSubscription, TelegramConnection
from .forms import MemeSubscriptionForm, TelegramConnectionForm
import json
import random
import string
from django.utils import timezone
from .models import MemeSubscription, TelegramConnection    
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

@login_required
def profile(request, username=None):
    """Страница профиля пользователя"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    # Статистика пользователя
    user_memes = Meme.objects.filter(author=user, is_published=True)
    user_favorites = Favorite.objects.filter(
        user=user
    ).select_related('meme').order_by('-created_at')
    
    # Получаем мемы из избранного
    favorite_memes = [fav.meme for fav in user_favorites if fav.meme.is_published]
    
    # Популярные теги пользователя
    from memes.models import Tag
    user_tags = Tag.objects.filter(
        memes__author=user
    ).annotate(
        meme_count=Count('memes')
    ).order_by('-meme_count')[:10]
    
    context = {
        'profile_user': user,
        'user_memes': user_memes[:6],
        'user_favorites': favorite_memes[:6],  # Последние 6 избранных
        'memes_count': user_memes.count(),
        'likes_received': sum(meme.likes_count for meme in user_memes),
        'user_tags': user_tags,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def favorites(request):
    """Страница избранного пользователя"""
    favorites_list = Favorite.objects.filter(
        user=request.user
    ).select_related('meme').order_by('-created_at')
    
    # Фильтруем только опубликованные мемы
    memes = [fav.meme for fav in favorites_list if fav.meme.is_published]
    
    context = {
        'favorite_memes': memes,
        'favorites_count': len(memes),
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

def user_memes(request, user_id):
    user = get_object_or_404(User, id=user_id)

@csrf_exempt
@login_required
def save_subscription_ajax(request):
    """Сохранение настроек подписки через AJAX"""
    if request.method == 'POST':
        try:
            # Пробуем получить JSON
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                # Если не JSON, пробуем FormData
                data = {
                    'channel': request.POST.get('channel', 'email'),
                    'frequency': request.POST.get('frequency', 'weekly')
                }
            
            channel = data.get('channel', 'email')
            frequency = data.get('frequency', 'weekly')
            
            # Получаем или создаем подписку
            from .models import MemeSubscription
            subscription, created = MemeSubscription.objects.get_or_create(
                user=request.user,
                defaults={
                    'channel': channel,
                    'frequency': frequency,
                    'is_active': True if frequency != 'none' else False
                }
            )
            
            # Обновляем подписку
            subscription.channel = channel
            subscription.frequency = frequency
            subscription.is_active = True if frequency != 'none' else False
            subscription.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Настройки подписки сохранены!',
                'data': {
                    'channel': channel,
                    'frequency': frequency,
                    'is_active': subscription.is_active
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Произошла ошибка при сохранении'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=400)

@login_required
def generate_telegram_code(request):
    """Генерация кода для привязки Telegram"""
    connection, created = TelegramConnection.objects.get_or_create(user=request.user)
    
    # Генерируем новый код
    code = ''.join(random.choices(string.digits, k=6))
    connection.verification_code = code
    connection.is_verified = False
    connection.save()
    
    return JsonResponse({
        'success': True,
        'code': code,
        'message': f'Ваш код для привязки Telegram: {code}'
    })


@csrf_exempt
@login_required
def verify_telegram_code(request):
    """Верификация Telegram кода"""
    if request.method == 'POST':
        data = json.loads(request.body)
        chat_id = data.get('chat_id')
        username = data.get('username')
        code = data.get('code')
        
        try:
            connection = TelegramConnection.objects.get(
                user=request.user,
                verification_code=code
            )
            connection.telegram_chat_id = chat_id
            connection.telegram_username = username
            connection.is_verified = True
            connection.verified_at = timezone.now()
            connection.save()
            
            return JsonResponse({'success': True, 'message': 'Telegram успешно привязан!'})
        except TelegramConnection.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Неверный код'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def unsubscribe_meme(request, token):
    """Отписка от рассылки по токену"""
    try:
        subscription = MemeSubscription.objects.get(user__profile__unsubscribe_token=token)
        subscription.is_active = False
        subscription.save()
        messages.success(request, 'Вы успешно отписались от рассылки.')
    except MemeSubscription.DoesNotExist:
        messages.error(request, 'Подписка не найдена.')
    
    return redirect('home')

@csrf_exempt
@login_required
def save_subscription_ajax(request):
    """Сохранение настроек подписки через AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            channel = data.get('channel', 'email')
            frequency = data.get('frequency', 'weekly')
            
            # Получаем или создаем подписку
            subscription, created = MemeSubscription.objects.get_or_create(
                user=request.user,
                defaults={
                    'channel': channel,
                    'frequency': frequency,
                    'is_active': True
                }
            )
            
            # Обновляем подписку
            subscription.channel = channel
            subscription.frequency = frequency
            subscription.is_active = True
            subscription.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Настройки подписки сохранены!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def check_telegram_connection(request):
    """Проверка статуса привязки Telegram"""
    try:
        connection = TelegramConnection.objects.get(user=request.user, is_verified=True)
        return JsonResponse({
            'connected': True,
            'telegram_username': connection.telegram_username,
            'connected_since': connection.verified_at.strftime('%d.%m.%Y')
        })
    except TelegramConnection.DoesNotExist:
        return JsonResponse({'connected': False})