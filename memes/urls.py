from django.urls import path, re_path
from . import views
from .views import moderation_queue
from .views_mailing import mailing_control, test_mailing, mailing_stats, api_mailing_status, api_run_mailing

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),
    
    # Детали мема
    path('meme/<int:pk>/', views.meme_detail, name='meme_detail'),
    path('memes/', views.meme_list, name='meme_list'),

    # Модерация
    path('my-memes/', views.my_memes, name='my_memes'),
    path('meme/<int:pk>/report/', views.report_meme, name='report_meme'),
    path('moderation/queue/', views.moderation_queue, name='moderation_queue'),

    # Управление жалобами
    path('staff/reports/', views.report_management, name='report_management'),
    path('staff/reports/<int:report_id>/resolve/', views.resolve_report, name='resolve_report'),
    path('staff/reports/<int:report_id>/delete/', views.delete_report, name='delete_report'),
    
    # Уведомления
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:pk>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/delete-all/', views.delete_all_notifications, name='delete_all_notifications'),
    
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
    path('memes/', views.meme_list, name='memes_list'),
    
    # AJAX endpoints
    path('meme/<int:pk>/like/', views.toggle_like, name='toggle_like'),
    path('meme/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    # Скачивание
    path('meme/<int:pk>/download/', views.download_meme, name='download_meme'),

    # Используем re_path для поддержки кириллицы в slug
    re_path(r'^tag/(?P<slug>[\w-]+)/$', views.tag_memes, name='tag_memes'),

    # Мониторинг активности
    path('staff/activity/', views.user_activity_dashboard, name='activity_dashboard'),
    
    # Детальная статистика по пользователю
    path('staff/activity/user/<int:user_id>/', views.user_activity_detail, name='user_activity_detail'),

    # Рассылка
    path('mailing/control/', mailing_control, name='mailing_control'),
    path('mailing/test/', test_mailing, name='test_mailing'),
    path('mailing/stats/', mailing_stats, name='mailing_stats'),
    path('api/mailing/status/', api_mailing_status, name='api_mailing_status'),
    path('api/mailing/run/<str:frequency>/', api_run_mailing, name='api_run_mailing'),
]