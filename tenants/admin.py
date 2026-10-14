from django.contrib import admin
from .models import TenantProfile, StaffProfile


@admin.register(TenantProfile)
class TenantProfileAdmin(admin.ModelAdmin):
    list_display  = ['business_name', 'user', 'business_type',
                     'tin_number', 'created_by', 'created_at']
    search_fields = ['business_name', 'user__email',
                     'user__first_name', 'tin_number']
    list_filter   = ['business_type']


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'mall', 'employee_id',
                     'department', 'date_employed']
    search_fields = ['user__email', 'employee_id']
    list_filter   = ['mall', 'department']