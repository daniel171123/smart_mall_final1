from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


@require_POST
@login_required
def mark_seen(request):
    request.user.notifications.filter(
        seen=False
    ).update(seen=True)
    return JsonResponse({'status': 'ok'})