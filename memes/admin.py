from django.contrib import admin
from django.utils.html import format_html
from .models import Meme, Tag, Like, Favorite

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
    list_display = ('title', 'author', 'created_at', 'likes_count', 'views_count', 'is_published', 'image_preview')
    list_filter = ('is_published', 'created_at', 'tags')
    search_fields = ('title', 'description', 'author__username')
    readonly_fields = ('created_at', 'updated_at', 'views_count', 'likes_count')
    filter_horizontal = ('tags',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: cover;" />')
        return "Нет изображения"
    image_preview.short_description = 'Превью'


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