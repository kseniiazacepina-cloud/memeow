from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Meme, Tag, Like, Favorite
from users.models import Profile

class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']

class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'email_subscription']

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с профилем"""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']

class MemeSerializer(serializers.ModelSerializer):
    """Основной сериализатор для мемов"""
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        many=True,
        write_only=True,
        required=False
    )
    is_liked = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Meme
        fields = [
            'id', 'title', 'image', 'description', 'author',
            'tags', 'tag_ids', 'created_at', 'views_count',
            'likes_count', 'is_published', 'is_liked', 'is_favorite'
        ]
        read_only_fields = ['author', 'views_count', 'likes_count', 'created_at']

    def get_is_liked(self, obj):
        """Проверяет, лайкнул ли текущий пользователь этот мем"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, meme=obj).exists()
        return False
    
    def get_is_favorite(self, obj):
        """Проверяет, добавлен ли мем в избранное текущим пользователем"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, meme=obj).exists()
        return False
    
    def create(self, validated_data):
        """Автоматически устанавливает автора при создании мема"""
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)
    
class LikeSerializer(serializers.ModelSerializer):
    """Сериализатор для лайков"""
    class Meta:
        model = Like
        fields = ['id', 'user', 'meme', 'created_at']
        read_only_fields = ['user']
        
class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного"""
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'meme', 'created_at']
        read_only_fields = ['user']