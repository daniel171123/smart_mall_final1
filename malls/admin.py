from django.contrib import admin
from .models import Mall, Shop


@admin.register(Mall)
class MallAdmin(admin.ModelAdmin):
    list_display  = ['name', 'city', 'contact_phone',
                     'contact_email', 'created_at']
    search_fields = ['name', 'city']


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display  = ['shop_number', 'mall', 'floor',
                     'shop_type', 'size_sqm', 'status']
    list_filter   = ['mall', 'floor', 'status', 'shop_type']
    search_fields = ['shop_number', 'mall__name']