from functools import wraps
from django.http import HttpResponseForbidden


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if not hasattr(request.user, 'profile'):
                return HttpResponseForbidden('โปรไฟล์ไม่พบ กรุณาติดต่อผู้ดูแลระบบ')
            if request.user.profile.role not in allowed_roles:
                return HttpResponseForbidden('คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
