from django.contrib import admin
from django.utils.html import format_html
from .models import Meme, Tag, Like, Favorite, Report, Notification, UserActivity
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Q
from datetime import datetime, timedelta

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
    list_display = ('meme', 'reporter', 'reason', 'is_resolved', 'created_at', 'resolved_at')
    list_filter = ('is_resolved', 'reason', 'created_at')
    search_fields = ('meme__title', 'reporter__username', 'description')
    readonly_fields = ('created_at', 'resolved_at')
    actions = ['mark_as_resolved', 'mark_as_unresolved']
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(
            is_resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f"{updated} жалоб отмечено как рассмотренные.")
    mark_as_resolved.short_description = "Отметить как рассмотренные"
    
    def mark_as_unresolved(self, request, queryset):
        updated = queryset.update(
            is_resolved=False,
            resolved_by=None,
            resolved_at=None,
            resolution_notes=''
        )
        self.message_user(request, f"{updated} жалоб отмечено как нерассмотренные.")
    mark_as_unresolved.short_description = "Отметить как нерассмотренные"

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

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'action_type_display', 'get_description', 
                    'ip_address', 'created_at_formatted', 'quick_actions')
    list_filter = ('action_type', 'created_at', 'user')
    search_fields = ('user__username', 'ip_address', 'description', 
                     'meme__title', 'user_agent')
    readonly_fields = ('created_at', 'user_agent_full', 'get_meme_link', 
                      'get_user_link', 'get_target_user_link')
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'action_type', 'description', 'ip_address')
        }),
        ('Связанные объекты', {
            'fields': ('meme', 'target_user'),
            'classes': ('collapse',)
        }),
        ('Техническая информация', {
            'fields': ('user_agent_full', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user(self, obj):
        return obj.user.username if obj.user else 'Аноним'
    get_user.short_description = 'Пользователь'
    
    def action_type_display(self, obj):
        colors = {
            'login': 'success',
            'logout': 'secondary',
            'view_meme': 'info',
            'like_meme': 'danger',
            'add_meme': 'primary',
            'report_meme': 'warning',
            'moderate': 'dark',
            'admin_action': 'danger',
        }
        color = colors.get(obj.action_type, 'secondary')
        return format_html(
            f'<span class="badge bg-{color}">{obj.get_action_type_display()}</span>'
        )
    action_type_display.short_description = 'Действие'
    
    def get_description(self, obj):
        return format_html(f'<small>{obj.description[:80]}</small>')
    get_description.short_description = 'Описание'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M:%S")
    created_at_formatted.short_description = 'Дата и время'
    
    def user_agent_full(self, obj):
        return format_html(f'<pre>{obj.user_agent}</pre>')
    user_agent_full.short_description = 'User Agent'
    
    def get_meme_link(self, obj):
        if obj.meme:
            url = reverse('admin:memes_meme_change', args=[obj.meme.id])
            return format_html(f'<a href="{url}">{obj.meme.title}</a>')
        return '-'
    get_meme_link.short_description = 'Мем'
    
    def get_user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html(f'<a href="{url}">{obj.user.username}</a>')
        return '-'
    get_user_link.short_description = 'Пользователь'
    
    def get_target_user_link(self, obj):
        if obj.target_user:
            url = reverse('admin:auth_user_change', args=[obj.target_user.id])
            return format_html(f'<a href="{url}">{obj.target_user.username}</a>')
        return '-'
    get_target_user_link.short_description = 'Целевой пользователь'
    
    def quick_actions(self, obj):
        links = []
        if obj.meme:
            links.append(f'<a href="{reverse("admin:memes_meme_change", args=[obj.meme.id])}" class="btn btn-sm btn-info">Мем</a>')
        if obj.user:
            links.append(f'<a href="{reverse("admin:auth_user_change", args=[obj.user.id])}" class="btn btn-sm btn-warning">Юзер</a>')
        return format_html(' '.join(links)) if links else '-'
    quick_actions.short_description = 'Быстрые действия'
    
    # Кастомные действия
    actions_on_top = True
    admin_actions = ['export_to_csv', 'cleanup_old_logs']
    
    def export_to_csv(self, request, queryset):
        """Экспорт выбранных записей в CSV"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="user_activity_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Пользователь', 'Действие', 'Описание', 'IP', 'Дата', 'Мем', 'User Agent'])
        
        for activity in queryset:
            writer.writerow([
                activity.user.username if activity.user else 'Аноним',
                activity.get_action_type_display(),
                activity.description,
                activity.ip_address,
                activity.created_at.strftime("%d.%m.%Y %H:%M:%S"),
                activity.meme.title if activity.meme else '',
                activity.user_agent[:100]
            ])
        
        return response
    export_to_csv.short_description = "📥 Экспорт в CSV"
    
    def cleanup_old_logs(self, request, queryset):
        """Удаление старых логов (старше 90 дней)"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=90)
        deleted_count, _ = UserActivity.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        self.message_user(request, f"Удалено {deleted_count} старых записей логов (старше 90 дней)")
    cleanup_old_logs.short_description = "🗑️ Очистить старые логи (90+ дней)"
    
    # Кастомная статистика на странице списка
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Статистика за последние 7 дней
        week_ago = timezone.now() - timedelta(days=7)
        
        stats = {
            'total_activities': UserActivity.objects.count(),
            'last_week': UserActivity.objects.filter(created_at__gte=week_ago).count(),
            'today': UserActivity.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'top_users': UserActivity.objects.filter(
                created_at__gte=week_ago
            ).values('user__username').annotate(
                count=Count('id')
            ).order_by('-count')[:10],
            'popular_actions': UserActivity.objects.filter(
                created_at__gte=week_ago
            ).values('action_type').annotate(
                count=Count('id')
            ).order_by('-count'),
        }
        
        extra_context['stats'] = stats
        return super().changelist_view(request, extra_context=extra_context)