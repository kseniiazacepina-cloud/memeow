from django.contrib import admin
from django.utils.html import format_html
from .models import Meme, Tag, Like, Favorite, Report, Notification
from django.utils import timezone

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_meme_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def get_meme_count(self, obj):
        return obj.memes.count()
    get_meme_count.short_description = 'Количество мемов'

@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'get_status', 'views_count', 'likes_count', 'created_at', 'image_preview')
    list_filter = ('moderation_status', 'is_published', 'created_at', 'tags')
    search_fields = ('title', 'description', 'author__username')
    readonly_fields = ('created_at', 'updated_at', 'views_count', 'likes_count')
    filter_horizontal = ('tags',)
    actions = ['approve_selected', 'reject_selected']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'image', 'description', 'tags', 'author')
        }),
        ('Статистика', {
            'fields': ('views_count', 'likes_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Модерация', {
            'fields': ('moderation_status', 'moderation_comment', 'moderated_by', 'moderated_at', 'is_published')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: cover;" />')
        return "Нет изображения"
    image_preview.short_description = 'Превью'
    
    def get_status(self, obj):
        color = obj.get_status_color()
        icon = obj.get_status_icon()
        return format_html(
            f'<span class="badge bg-{color}">{icon} {obj.get_moderation_status_display()}</span>'
        )
    get_status.short_description = 'Статус'
    
    def save_model(self, request, obj, form, change):
        """Отправляем уведомление при изменении статуса"""
        if change and 'moderation_status' in form.changed_data:
            # Отправляем уведомление автору
            from .utils import send_moderation_notification
            send_moderation_notification(obj, request.user)
            
            if obj.moderation_status == 'approved':
                obj.is_published = True
                obj.moderated_by = request.user
                obj.moderated_at = timezone.now()
            elif obj.moderation_status == 'rejected':
                obj.is_published = False
                obj.moderated_by = request.user
                obj.moderated_at = timezone.now()
        
        super().save_model(request, obj, form, change)
    
    def approve_selected(self, request, queryset):
        updated = 0
        for meme in queryset:
            meme.moderation_status = 'approved'
            meme.is_published = True
            meme.moderated_by = request.user
            meme.moderated_at = timezone.now()
            meme.save()
            
            # Отправляем уведомление
            from .utils import send_moderation_notification
            send_moderation_notification(meme, request.user)
            updated += 1
        
        self.message_user(request, f"{updated} мемов одобрено.")
    approve_selected.short_description = "Одобрить выбранные мемы"
    
    def reject_selected(self, request, queryset):
        for meme in queryset:
            meme.moderation_status = 'rejected'
            meme.is_published = False
            meme.moderated_by = request.user
            meme.moderated_at = timezone.now()
            meme.save()
            
            # Отправляем уведомление
            from .utils import send_moderation_notification
            send_moderation_notification(meme, request.user)
        
        self.message_user(request, f"{queryset.count()} мемов отклонено.")
    reject_selected.short_description = "Отклонить выбранные мемы"

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('meme', 'reporter', 'reason', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'reason', 'created_at')
    search_fields = ('meme__title', 'reporter__username', 'description')
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        for report in queryset:
            report.resolve(request.user, "Рассмотрено администратором")
        self.message_user(request, f"{queryset.count()} жалоб отмечено как рассмотренные.")
    mark_as_resolved.short_description = "Отметить как рассмотренные"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'meme', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'meme__title')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'meme', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'meme__title')