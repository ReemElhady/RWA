from django.core.exceptions import PermissionDenied

def group_required(*group_names):
    """
    Decorator for views that checks if the logged-in user belongs to any of the required groups.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied

            if request.user.is_superuser:  # Always allow superusers
                return view_func(request, *args, **kwargs)

            if bool(request.user.groups.filter(name__in=group_names)):
                return view_func(request, *args, **kwargs)

            raise PermissionDenied
        return _wrapped_view
    return decorator
