from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['recipient', 'notification_type',
                     'channel', 'is_sent', 'sent_at', 'created_at']
    list_filter   = ['notification_type', 'channel', 'is_sent']
    search_fields = ['recipient__email', 'subject']
    readonly_fields = ['sent_at', 'created_at']