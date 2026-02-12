import socket
from django.utils import timezone
from .models import UserActivity

class UserActivityMiddleware:
    """Middleware для отслеживания активности пользователей"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Получаем IP адрес
        ip_address = self.get_client_ip(request)
        
        # Обрабатываем запрос
        response = self.get_response(request)
        
        # Логируем активность
        self.log_activity(request, ip_address)
        
        return response
    
    def get_client_ip(self, request):
        """Получаем реальный IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def log_activity(self, request, ip_address):
        """Логирует активность пользователя"""
        try:
            user = request.user if request.user.is_authenticated else None
            path = request.path
            
            # Определяем тип действия по пути
            action_type = self.get_action_type(path, request.method)
            
            if action_type:
                description = f"{request.method} {path}"
                
                # Для конкретных действий добавляем детали
                if '/meme/' in path and request.method == 'GET':
                    meme_id = path.split('/meme/')[1].split('/')[0]
                    from .models import Meme
                    try:
                        meme = Meme.objects.get(id=meme_id)
                        description = f"Просмотр мема: {meme.title}"
                    except:
                        meme = None
                elif '/like/' in path or '/favorite/' in path:
                    description = f"Взаимодействие с мемом: {path}"
                
                # Создаем запись активности
                UserActivity.objects.create(
                    user=user,
                    ip_address=ip_address,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    action_type=action_type,
                    description=description,
                )
        
        except Exception as e:
            # Не прерываем выполнение при ошибке логирования
            print(f"Error logging activity: {e}")
    
    def get_action_type(self, path, method):
        """Определяет тип действия по пути и методу"""
        if '/login/' in path and method == 'POST':
            return 'login'
        elif '/logout/' in path:
            return 'logout'
        elif '/register/' in path and method == 'POST':
            return 'register'
        elif '/meme/' in path and method == 'GET':
            return 'view_meme'
        elif '/add_meme/' in path:
            return 'add_meme'
        elif '/edit_meme/' in path:
            return 'edit_meme'
        elif '/search/' in path:
            return 'search'
        elif '/admin/' in path:
            return 'admin_action'
        elif '/moderation/' in path or path.endswith('moderation_queue/'):
            return 'moderate'
        return None