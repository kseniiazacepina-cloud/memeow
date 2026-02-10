from memes.management.commands.send_meme_digest import Command as SendDigestCommand

def send_daily_digest():
    """Ежедневная рассылка в 10:00"""
    command = SendDigestCommand()
    command.handle(frequency='daily')

def send_weekly_digest():
    """Еженедельная рассылка по понедельникам в 10:00"""
    command = SendDigestCommand()
    command.handle(frequency='weekly')