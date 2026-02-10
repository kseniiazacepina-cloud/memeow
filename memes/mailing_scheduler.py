import threading
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

class MailingScheduler:
    """Планировщик рассылок"""
    
    def __init__(self):
        self.scheduler_running = False
        self.scheduler_thread = None
        self.daily_hour = 10  # Час ежедневной рассылки
        self.daily_minute = 0  # Минута ежедневной рассылки
        
    def start(self):
        """Запуск планировщика"""
        if not self.scheduler_running:
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("Менеджер рассылок запущен")
    
    def stop(self):
        """Остановка планировщика"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Менеджер рассылок остановлен")
    
    def _run_scheduler(self):
        """Запуск планировщика в отдельном потоке"""
        logger.info(f"Планировщик запущен. Ежедневная рассылка в {self.daily_hour:02d}:{self.daily_minute:02d}")
        
        # Бесконечный цикл планировщика
        while self.scheduler_running:
            try:
                now = datetime.now()
                
                # Проверяем, пора ли отправлять ежедневную рассылку
                if now.hour == self.daily_hour and now.minute == self.daily_minute and now.second == 0:
                    self._send_daily_digest()
                
                # Проверяем, понедельник ли и пора ли отправлять еженедельную
                if (now.weekday() == 0 and  # Понедельник
                    now.hour == self.daily_hour and 
                    now.minute == self.daily_minute and 
                    now.second == 0):
                    self._send_weekly_digest()
                
                time.sleep(1)  # Проверяем каждую секунду
                
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
                time.sleep(60)  # Ждем минуту при ошибке
    
    def _send_daily_digest(self):
        """Отправка ежедневной рассылки"""
        try:
            logger.info(f"[{datetime.now()}] Запуск ежедневной рассылки...")
            call_command('send_meme_digest', 'daily')
            logger.info(f"[{datetime.now()}] Ежедневная рассылка завершена")
        except Exception as e:
            logger.error(f"Ошибка при отправке ежедневной рассылки: {e}")
    
    def _send_weekly_digest(self):
        """Отправка еженедельной рассылки"""
        try:
            logger.info(f"[{datetime.now()}] Запуск еженедельной рассылки...")
            call_command('send_meme_digest', 'weekly')
            logger.info(f"[{datetime.now()}] Еженедельная рассылка завершена")
        except Exception as e:
            logger.error(f"Ошибка при отправке еженедельной рассылки: {e}")
    
    def run_now(self, frequency='daily'):
        """Немедленный запуск рассылки"""
        if frequency == 'daily':
            self._send_daily_digest()
        elif frequency == 'weekly':
            self._send_weekly_digest()
        else:
            logger.error(f"Неизвестная частота: {frequency}")
    
    def set_time(self, hour, minute):
        """Установить время ежедневной рассылки"""
        self.daily_hour = int(hour)
        self.daily_minute = int(minute)
        logger.info(f"Время ежедневной рассылки изменено на {self.daily_hour:02d}:{self.daily_minute:02d}")
    
    def get_status(self):
        """Получить статус планировщика"""
        now = datetime.now()
        
        # Следующая ежедневная рассылка
        next_daily = now.replace(hour=self.daily_hour, minute=self.daily_minute, second=0, microsecond=0)
        if now >= next_daily:
            next_daily += timedelta(days=1)
        
        # Следующая еженедельная (в понедельник)
        days_until_monday = (7 - now.weekday()) % 7 or 7
        next_monday = now + timedelta(days=days_until_monday)
        next_weekly = next_monday.replace(hour=self.daily_hour, minute=self.daily_minute, second=0, microsecond=0)
        
        return {
            'running': self.scheduler_running,
            'daily_time': f"{self.daily_hour:02d}:{self.daily_minute:02d}",
            'next_daily': next_daily.strftime('%d.%m.%Y %H:%M'),
            'next_weekly': next_weekly.strftime('%d.%m.%Y %H:%M'),
        }

# Глобальный экземпляр планировщика
mailing_scheduler = MailingScheduler()