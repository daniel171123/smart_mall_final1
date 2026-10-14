from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['invoice', 'tenant', 'amount_paid',
                     'payment_method', 'status', 'submitted_at']
    list_filter   = ['status', 'payment_method']
    search_fields = ['invoice__invoice_number',
                     'tenant__business_name',
                     'transaction_reference']
    readonly_fields = ['submitted_at', 'verified_at']