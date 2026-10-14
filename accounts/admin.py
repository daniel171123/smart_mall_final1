
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AuditLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model         = CustomUser
    list_display  = [
        "email", "first_name", "last_name",
        "role", "is_active", "date_joined"
    ]
    list_filter   = ["role", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    ordering      = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {
            "fields": (
                "first_name", "last_name", "phone_number"
            )
        }),
        ("Role & Access", {
            "fields": (
                "role", "is_active", "is_staff",
                "is_superuser", "must_change_password"
            )
        }),
        ("Permissions", {
            "fields": ("groups", "user_permissions")
        }),
        ("Important Dates", {
            "fields": ("date_joined", "last_login")
        }),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "first_name", "last_name",
                "phone_number", "role",
                "password1", "password2",
                "is_active", "is_staff",
            ),
        }),
    )
    readonly_fields = ["date_joined"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = [
        "timestamp", "user", "action", "ip_address"
    ]
    list_filter   = ["action"]
    search_fields = ["user__email", "action", "details"]
    readonly_fields = [
        "user", "action", "details",
        "ip_address", "timestamp"
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
