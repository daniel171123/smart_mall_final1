from django.contrib import admin
from .models import Lease


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'shop', 'monthly_rent',
                     'start_date', 'end_date', 'status']
    list_filter   = ['status', 'shop__mall']
    search_fields = ['tenant__business_name',
                     'shop__shop_number']
    readonly_fields = ['created_at', 'terminated_at']