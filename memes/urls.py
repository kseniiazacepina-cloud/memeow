from django.urls import path
from . import views
from .views import (
    home, meme_detail, add_meme, edit_meme, delete_meme,
    tag_memes, search, toggle_like, toggle_favorite,
    random_meme, popular_memes, download_meme
)

urlpatterns = [
    # Главная страница
    path('', home, name='home'),
    
    # Детали мема
    path('meme/<int:pk>/', meme_detail, name='meme_detail'),
    
    # Добавление/редактирование мемов
    path('meme/add/', add_meme, name='add_meme'),
    path('meme/<int:pk>/edit/', edit_meme, name='edit_meme'),
    path('meme/<int:pk>/delete/', delete_meme, name='delete_meme'),
    
    # Теги
    path('tag/<slug:slug>/', tag_memes, name='tag_memes'),
    
    # Поиск
    path('search/', search, name='search'),
    
    # Случайный мем
    path('random/', random_meme, name='random_meme'),
    
    # Популярные мемы
    path('popular/', popular_memes, name='popular_memes'),
    
    # AJAX endpoints
    path('meme/<int:pk>/like/', toggle_like, name='toggle_like'),
    path('meme/<int:pk>/favorite/', toggle_favorite, name='toggle_favorite'),
    
    # Скачивание
    path('meme/<int:pk>/download/', download_meme, name='download_meme'),
]