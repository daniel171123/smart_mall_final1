
from django.utils import timezone


def audit_log(user, action, details="", request=None):
    """
    Records every sensitive system action.
    Called directly from views after key operations.
    """
    from accounts.models import AuditLog
    ip = None
    if request:
        x_forwarded = request.META.get(
            "HTTP_X_FORWARDED_FOR", ""
        )
        ip = (
            x_forwarded.split(",")[0].strip()
            if x_forwarded
            else request.META.get("REMOTE_ADDR", "")
        )
    AuditLog.objects.create(
        user=user,
        action=action,
        details=details,
        ip_address=ip or "",
        timestamp=timezone.now(),
    )
