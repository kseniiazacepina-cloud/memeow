from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    """Инлайн-админка для профиля"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    """Кастомизированная админка пользователя с профилем"""
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_email_subscription')
    list_select_related = ('profile',)
    
    def get_email_subscription(self, instance):
        return instance.profile.email_subscription
    get_email_subscription.short_description = 'Подписка'
    get_email_subscription.boolean = True
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# Перерегистрируем UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)