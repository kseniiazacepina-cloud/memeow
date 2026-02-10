from django import template

register = template.Library()

@register.filter
def get_activity_color(action_type):
    colors = {
        'login': 'success',
        'logout': 'secondary', 
        'view_meme': 'info',
        'like_meme': 'danger',
        'report_meme': 'warning',
        'moderate': 'dark',
        'admin_action': 'danger',
    }
    return colors.get(action_type, 'secondary')