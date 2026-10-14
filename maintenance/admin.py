from django.contrib import admin
from .models import MaintenanceRequest


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display  = ['title', 'shop', 'requested_by',
                     'priority', 'status', 'assigned_to',
                     'created_at']
    list_filter   = ['status', 'priority', 'shop__mall']
    search_fields = ['title', 'shop__shop_number']
    readonly_fields = ['created_at', 'completed_at']