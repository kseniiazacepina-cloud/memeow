from django.apps import AppConfig

class MemesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'memes'

    def ready(self):
        """Запуск при инициализации приложения"""
        # Для начала не будем запускать планировщик автоматически
        # Пользователь сам запустит его через веб-интерфейс
        pass