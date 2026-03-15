from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {
            'unread_notifications': [],
            'unread_count': 0,
        }

    unread = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')

    return {
        'unread_notifications': unread[:5],  # แสดงแค่ 5 อันใน navbar
        'unread_count': unread.count(),
    }


def user_role(request):
    if not request.user.is_authenticated:
        return {
            'user_role': None,
            'user_department': None,
        }

    profile = getattr(request.user, 'profile', None)

    return {
        'user_role': profile.role if profile else None,
        'user_department': profile.department if profile else None,
    }
