from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import random
from django.core.cache import cache
from django.contrib.auth.models import User

from ..models import Meme, Tag, Like, Favorite
from ..serializers import MemeSerializer, TagSerializer, LikeSerializer, FavoriteSerializer

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """API для работы с тегами (только чтение)"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class MemeViewSet(viewsets.ModelViewSet):
    """Основной API для работы с мемами"""
    queryset = Meme.objects.filter(is_published=True).select_related('author').prefetch_related('tags')
    serializer_class = MemeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Дополнительная фильтрация и оптимизация запросов"""
        queryset = super().get_queryset()
        
        # Фильтрация по тегу
        tag_slug = self.request.query_params.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Поиск по названию и описанию
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        # Сортировка
        sort = self.request.query_params.get('sort', '-created_at')
        if sort in ['-created_at', 'created_at', '-likes_count', 'views_count']:
            queryset = queryset.order_by(sort)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def random(self, request):
        """Получить случайный мем"""
        count = self.get_queryset().count()
        if count == 0:
            return Response({'detail': 'Нет доступных мемов'}, status=404)
        
        random_index = random.randint(0, count - 1)
        random_meme = self.get_queryset()[random_index]
        serializer = self.get_serializer(random_meme)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def meme_of_the_day(self, request):
        """Получить мем дня (общий для всех)"""
        cache_key = 'meme_of_the_day'
        meme = cache.get(cache_key)
        
        if not meme:
            # Выбираем случайный мем из популярных за последнюю неделю
            week_ago = timezone.now() - timedelta(days=7)
            popular_memes = Meme.objects.filter(
                is_published=True,
                created_at__gte=week_ago
            ).order_by('-likes_count')[:10]
            
            if popular_memes.exists():
                meme = random.choice(popular_memes)
                # Кэшируем на 24 часа
                cache.set(cache_key, meme, 60 * 60 * 24)
            else:
                # Если нет популярных, берем случайный
                count = Meme.objects.filter(is_published=True).count()
                if count > 0:
                    random_index = random.randint(0, count - 1)
                    meme = Meme.objects.filter(is_published=True)[random_index]
                    cache.set(cache_key, meme, 60 * 60 * 24)
        
        if meme:
            serializer = self.get_serializer(meme)
            return Response(serializer.data)
        return Response({'detail': 'Мем дня не найден'}, status=404)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def personal_meme_of_the_day(self, request):
        """Персональный мем дня для авторизованного пользователя"""
        user = request.user
        cache_key = f'personal_meme_of_the_day_{user.id}'
        meme = cache.get(cache_key)
        
        if not meme:
            # Логика для персональных рекомендаций
            # Вариант 1: на основе любимых тегов пользователя
            user_liked_tags = Tag.objects.filter(
                memes__like_records__user=user
            ).distinct()
            
            if user_liked_tags.exists():
                # Берем мемы с тегами, которые пользователь лайкал
                recommended_memes = Meme.objects.filter(
                    is_published=True,
                    tags__in=user_liked_tags
                ).exclude(
                    like_records__user=user  # Исключаем уже лайкнутые
                ).distinct()
                
                if recommended_memes.exists():
                    meme = random.choice(recommended_memes)
                else:
                    # Если нет рекомендаций, берем случайный
                    count = Meme.objects.filter(is_published=True).count()
                    if count > 0:
                        random_index = random.randint(0, count - 1)
                        meme = Meme.objects.filter(is_published=True)[random_index]
            else:
                # Если у пользователя нет лайков, берем случайный мем
                count = Meme.objects.filter(is_published=True).count()
                if count > 0:
                    random_index = random.randint(0, count - 1)
                    meme = Meme.objects.filter(is_published=True)[random_index]
            
            if meme:
                # Кэшируем на 24 часа
                cache.set(cache_key, meme, 60 * 60 * 24)
        
        if meme:
            serializer = self.get_serializer(meme)
            return Response(serializer.data)
        return Response({'detail': 'Персональный мем дня не найден'}, status=404)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Поставить или убрать лайк с мема"""
        meme = self.get_object()
        user = request.user
        
        like, created = Like.objects.get_or_create(user=user, meme=meme)
        
        if not created:
            # Если лайк уже существует - удаляем (убираем лайк)
            like.delete()
            meme.likes_count -= 1
            liked = False
        else:
            meme.likes_count += 1
            liked = True
        
        meme.save()
        
        return Response({
            'liked': liked,
            'likes_count': meme.likes_count
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить или удалить мем из избранного"""
        meme = self.get_object()
        user = request.user
        
        favorite, created = Favorite.objects.get_or_create(user=user, meme=meme)
        
        if not created:
            # Если уже в избранном - удаляем
            favorite.delete()
            favorited = False
        else:
            favorited = True
        
        return Response({
            'favorited': favorited
        })


class LikeViewSet(viewsets.ModelViewSet):
    """API для управления лайками"""
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Like.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FavoriteViewSet(viewsets.ModelViewSet):
    """API для управления избранным"""
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('meme')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StatsView(generics.GenericAPIView):
    """API для получения статистики"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        # Популярные мемы (по лайкам)
        popular_memes = Meme.objects.filter(
            is_published=True
        ).order_by('-likes_count')[:10]
        
        # Самые активные пользователи
        active_users = User.objects.annotate(
            meme_count=Count('memes'),
            like_count=Count('likes')
        ).order_by('-meme_count')[:5]
        
        # Популярные теги
        popular_tags = Tag.objects.annotate(
            meme_count=Count('memes')
        ).order_by('-meme_count')[:10]
        
        meme_serializer = MemeSerializer(popular_memes, many=True, context={'request': request})
        
        return Response({
            'popular_memes': meme_serializer.data,
            'active_users': [
                {
                    'username': user.username,
                    'meme_count': user.meme_count,
                    'like_count': user.like_count
                }
                for user in active_users
            ],
            'popular_tags': TagSerializer(popular_tags, many=True).data
        })