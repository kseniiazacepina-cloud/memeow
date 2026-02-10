from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.management import call_command

# Простой планировщик (без сложной логики потоков)
class SimpleScheduler:
    def __init__(self):
        self.running = False
        self.daily_hour = 10
        self.daily_minute = 0
    
    def start(self):
        self.running = True
    
    def stop(self):
        self.running = False
    
    def set_time(self, hour, minute):
        self.daily_hour = int(hour)
        self.daily_minute = int(minute)
    
    def get_status(self):
        from datetime import datetime, timedelta
        
        now = datetime.now()
        next_daily = now.replace(hour=self.daily_hour, minute=self.daily_minute, second=0, microsecond=0)
        if now >= next_daily:
            next_daily += timedelta(days=1)
        
        days_until_monday = (7 - now.weekday()) % 7 or 7
        next_monday = now + timedelta(days=days_until_monday)
        next_weekly = next_monday.replace(hour=self.daily_hour, minute=self.daily_minute, second=0, microsecond=0)
        
        return {
            'running': self.running,
            'daily_time': f"{self.daily_hour:02d}:{self.daily_minute:02d}",
            'next_daily': next_daily.strftime('%d.%m.%Y %H:%M'),
            'next_weekly': next_weekly.strftime('%d.%m.%Y %H:%M'),
        }

# Создаем экземпляр планировщика
scheduler = SimpleScheduler()

@user_passes_test(lambda u: u.is_staff)
def mailing_control(request):
    """Панель управления рассылкой"""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'start':
            scheduler.start()
            messages.success(request, 'Планировщик рассылок запущен')
            
        elif action == 'stop':
            scheduler.stop()
            messages.success(request, 'Планировщик рассылок остановлен')
            
        elif action == 'send_daily':
            try:
                call_command('send_meme_digest', 'daily')
                messages.success(request, 'Ежедневная рассылка отправлена')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
                
        elif action == 'send_weekly':
            try:
                call_command('send_meme_digest', 'weekly')
                messages.success(request, 'Еженедельная рассылка отправлена')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
                
        elif action == 'set_time':
            hour = request.POST.get('hour')
            minute = request.POST.get('minute')
            if hour and minute:
                scheduler.set_time(hour, minute)
                messages.success(request, f'Время рассылки изменено на {hour}:{minute}')
                
        return redirect('mailing_control')
    
    # Статистика
    from users.models import MemeSubscription
    stats = {
        'daily_subscribers': MemeSubscription.objects.filter(
            frequency='daily', is_active=True
        ).count(),
        'weekly_subscribers': MemeSubscription.objects.filter(
            frequency='weekly', is_active=True
        ).count(),
        'total_subscribers': MemeSubscription.objects.filter(is_active=True).count(),
    }
    
    context = {
        'scheduler_status': scheduler.get_status(),
        'stats': stats,
        'now': timezone.now(),
    }
    
    return render(request, 'memes/mailing_control.html', context)

@login_required
def test_mailing(request):
    """Отправить тестовое письмо текущему пользователю"""
    if request.method == 'POST':
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        
        try:
            # Получаем несколько мемов для теста
            from memes.models import Meme
            recent_memes = Meme.objects.filter(
                is_published=True
            ).order_by('-created_at')[:3]
            
            context = {
                'user': request.user,
                'recent_memes': recent_memes,
                'site_url': 'http://localhost:8000',
            }
            
            # HTML версия
            html_message = render_to_string('emails/test_email.html', context)
            
            # Отправляем письмо
            send_mail(
                'Тестовое письмо от Memeow',
                'Это тестовое письмо.',
                'memeowsubscription@gmail.com',
                [request.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            messages.success(request, f'Тестовое письмо отправлено на {request.user.email}')
            
        except Exception as e:
            messages.error(request, f'Ошибка отправки: {str(e)}')
        
        return redirect('profile')
    
    return render(request, 'memes/test_mailing.html')

@user_passes_test(lambda u: u.is_staff)
def api_mailing_status(request):
    """API для получения статуса рассылки"""
    return JsonResponse(scheduler.get_status())

@user_passes_test(lambda u: u.is_staff)
def api_run_mailing(request, frequency):
    """API для запуска рассылки"""
    if frequency in ['daily', 'weekly']:
        try:
            if frequency == 'daily':
                call_command('send_meme_digest', 'daily')
                return JsonResponse({'success': True, 'message': 'Ежедневная рассылка запущена'})
            else:
                call_command('send_meme_digest', 'weekly')
                return JsonResponse({'success': True, 'message': 'Еженедельная рассылка запущена'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid frequency'})

@user_passes_test(lambda u: u.is_staff)
def mailing_stats(request):
    """Статистика рассылок"""
    from users.models import MemeSubscription
    from django.db.models import Count
    
    # Распределение по частоте
    frequency_stats = MemeSubscription.objects.filter(
        is_active=True
    ).values('frequency').annotate(
        count=Count('id')
    ).order_by('frequency')
    
    # Последние 10 рассылок (из логов UserActivity)
    from users.models import UserActivity
    recent_mailings = UserActivity.objects.filter(
        action_type__in=['email_digest_sent', 'bulk_email_sent']
    ).order_by('-created_at')[:10]
    
    context = {
        'frequency_stats': frequency_stats,
        'recent_mailings': recent_mailings,
        'total_users': MemeSubscription.objects.count(),
        'active_users': MemeSubscription.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'memes/mailing_stats.html', context)