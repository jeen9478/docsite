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
