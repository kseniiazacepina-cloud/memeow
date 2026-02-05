from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views import profile, favorites, settings_view, dashboard
from users import views as user_views

urlpatterns = [
    # Профиль пользователя
    path('profile/', profile, name='profile'),
    path('profile/<str:username>/', profile, name='user_profile'),
    
    # Настройки
    path('settings/', settings_view, name='settings'),
    
    # Избранное
    path('favorites/', favorites, name='favorites'),
    
    # Панель управления
    path('dashboard/', dashboard, name='dashboard'),
    
    # Аутентификация (переопределяем стандартные URL для своих шаблонов)
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(
        template_name='registration/logout.html'
    ), name='logout'),
    
    path('accounts/profile/', user_views.profile, name='profile'),
    path('register/', views.register, name='register'),
    
    # Восстановление пароля
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ), name='password_reset_confirm'),
    
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]

# Добавляем view для регистрации
from .views import register
urlpatterns.append(path('register/', register, name='register'))