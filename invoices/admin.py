from django.contrib import admin
from .models import Invoice, PenaltyLog


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display  = ['invoice_number', 'lease', 'total_amount',
                     'issue_date', 'due_date', 'status']
    list_filter   = ['status', 'generated_automatically',
                     'issue_date']
    search_fields = ['invoice_number',
                     'lease__tenant__business_name']
    readonly_fields = ['invoice_number', 'created_at']


@admin.register(PenaltyLog)
class PenaltyLogAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'date', 'days_overdue',
                    'daily_penalty_rate', 'cumulative_penalty']
    list_filter  = ['date']