from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string

class Command(BaseCommand):
    help = 'Отправка тестового письма для проверки конфигурации email'
    
    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email адрес для отправки теста')
    
    def handle(self, *args, **options):
        test_email = options['email']
        
        self.stdout.write('Проверка конфигурации email...')
        self.stdout.write(f'От кого: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Кому: {test_email}')
        self.stdout.write(f'Email бэкенд: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Email хост: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        
        try:
            # Простой тест
            self.stdout.write('\n--- Тест 1: Простое текстовое письмо ---')
            result = send_mail(
                subject='Тестовое письмо от Memeow',
                message='Это тестовое письмо от Memeow. Если вы получили это письмо, значит конфигурация email работает корректно.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                fail_silently=False,
            )
            self.stdout.write(f'Результат: {result} (1 = успешно)')
            
            # Тест с HTML
            self.stdout.write('\n--- Тест 2: HTML письмо ---')
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                    }
                    .header {
                        background-color: #4a6fa5;
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }
                    .content {
                        padding: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Тестовое HTML письмо</h1>
                </div>
                <div class="content">
                    <p>Это <strong>тестовое HTML письмо</strong> от Memeow.</p>
                    <p>Если вы видите это письмо, значит HTML письма работают корректно.</p>
                    <p style="color: blue;">Пример синего текста</p>
                    <p>🎉 Поздравляем! Email система работает!</p>
                </div>
            </body>
            </html>
            """
            
            email = EmailMultiAlternatives(
                subject='Тестовое HTML письмо от Memeow',
                body='Текстовая версия письма. Если вы видите это, значит ваш почтовый клиент не поддерживает HTML.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[test_email],
            )
            email.attach_alternative(html_content, "text/html")
            
            result = email.send()
            self.stdout.write(f'Результат: {result} (1 = успешно)')
            
            # Тест с вложением
            self.stdout.write('\n--- Тест 3: Письмо с вложением ---')
            try:
                # Создаем тестовый файл
                test_file_content = 'Это содержимое тестового вложения. Создано системой Memeow.'.encode('utf-8')
                
                email = EmailMultiAlternatives(
                    subject='Тестовое письмо с вложением от Memeow',
                    body='Это письмо содержит тестовое вложение.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[test_email],
                )
                
                email.attach('тестовое_вложение.txt', test_file_content, 'text/plain')
                
                result = email.send()
                self.stdout.write(f'Результат: {result} (1 = успешно)')
            except Exception as e:
                self.stdout.write(f'Тест с вложением не удался: {e}')
            
            
            self.stdout.write(self.style.SUCCESS('\n✅ Все тесты завершены успешно!'))
            