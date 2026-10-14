
def recent_notifications(request):
    """
    WHY: Makes recent notifications available in
    every template automatically via context processor.
    The topbar notification bell uses this data.
    """
    if not request.user.is_authenticated:
        return {"recent_notifications": [], "unread_count": 0}
    try:
        notifs = request.user.notifications.filter(
            is_sent=True
        ).order_by("-sent_at")[:8]
        unread = request.user.notifications.filter(
            is_sent=True, seen=False
        ).count()
        return {
            "recent_notifications": notifs,
            "unread_count": unread,
        }
    except Exception:
        return {"recent_notifications": [], "unread_count": 0}
