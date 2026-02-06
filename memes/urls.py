from django.urls import path
from . import views

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),
    
    # Детали мема
    path('meme/<int:pk>/', views.meme_detail, name='meme_detail'),
    path('memes/', views.meme_list, name='meme_list'),
    
    # Добавление/редактирование мемов
    path('meme/add/', views.add_meme, name='add_meme'),
    path('meme/<int:pk>/edit/', views.edit_meme, name='edit_meme'),
    path('meme/<int:pk>/delete/', views.delete_meme, name='delete_meme'),
    
    # Теги
    path('tag/<slug:slug>/', views.tag_memes, name='tag_memes'),
    
    # Поиск
    path('search/', views.search, name='search'),
    
    # Случайный мем
    path('random/', views.random_meme, name='random_meme'),
    
    # Популярные мемы
    path('popular/', views.popular_memes, name='popular_memes'),
    
    # AJAX endpoints
    path('meme/<int:pk>/like/', views.toggle_like, name='toggle_like'),
    path('meme/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    # Скачивание
    path('meme/<int:pk>/download/', views.download_meme, name='download_meme'),
]