"""
URL configuration for M project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularSwaggerView
from django.contrib.auth import views as auth_views
from users import views as user_views

urlpatterns = [
    # Админ-панель
    path('admin/', admin.site.urls),
    
    # API
    path('api/', include('memes.api.urls')),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Веб-интерфейс
    path('', include('memes.urls')),  # Основные страницы мемов
    path('users/', include('users.urls')),  # Профили пользователей
    path('accounts/', include('django.contrib.auth.urls')),  # Стандартная аутентификация
    path('accounts/profile/', user_views.profile, name='profile'),
    
    # Перенаправление корня на главную
    path('', RedirectView.as_view(pattern_name='home', permanent=False)),
]

# Для обслуживания медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Настройка заголовков админ-панели
admin.site.site_header = "Memeow Администрация"
admin.site.site_title = "Memeow Admin"
admin.site.index_title = "Добро пожаловать в админ-панель Memeow"
