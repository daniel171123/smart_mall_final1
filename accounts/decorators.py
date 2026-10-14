from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def role_required(*roles):
    """
    WHY: Single decorator that:
    1. Checks user is logged in
    2. Checks user has the required role
    3. Redirects with a clear message if not

    Usage:
        @role_required('MANAGER', 'SUPER_ADMIN')
        def my_view(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.must_change_password:
                return redirect('accounts:change_password')
            if request.user.role not in roles:
                messages.error(
                    request,
                    'You do not have permission to access '
                    'that page.'
                )
                return redirect('dashboard:home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator