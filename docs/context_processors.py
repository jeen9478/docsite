from .models import Notification


def notifications(request):
    if request.user.is_authenticated:
        unread = Notification.objects.filter(
            user=request.user, is_read=False
        ).order_by('-created_at')
        return {
            'unread_notifications': unread,
            'unread_count': unread.count(),
        }
    return {
        'unread_notifications': [],
        'unread_count': 0,
    }


def user_role(request):
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        return {
            'user_role': request.user.profile.role,
            'user_department': request.user.profile.department,
        }
    return {
        'user_role': None,
        'user_department': None,
    }
