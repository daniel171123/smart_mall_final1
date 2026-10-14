from django.contrib import admin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display  = ['subject', 'tenant', 'complaint_type',
                     'status', 'assigned_to', 'created_at']
    list_filter   = ['status', 'complaint_type']
    search_fields = ['subject', 'tenant__business_name']
    readonly_fields = ['created_at', 'resolved_at']