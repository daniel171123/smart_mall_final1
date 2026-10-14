
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin
)
from django.db import models
from django.utils import timezone
from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        MANAGER     = "MANAGER",     "Manager"
        FINANCE     = "FINANCE",     "Finance Officer"
        TENANT      = "TENANT",      "Tenant"

    email        = models.EmailField(unique=True)
    first_name   = models.CharField(max_length=100)
    last_name    = models.CharField(max_length=100)
    phone_number = models.CharField(
        max_length=20, blank=True
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TENANT
    )
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(
        default=timezone.now
    )
    must_change_password = models.BooleanField(
        default=True
    )

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name        = "User"
        verbose_name_plural = "Users"
        ordering            = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_finance(self):
        return self.role == self.Role.FINANCE

    @property
    def is_tenant_user(self):
        return self.role == self.Role.TENANT

    @property
    def is_staff_member(self):
        return self.role in [
            self.Role.SUPER_ADMIN,
            self.Role.MANAGER,
            self.Role.FINANCE,
        ]


class AuditLog(models.Model):
    """
    WHY: Every sensitive financial operation must
    be logged. This gives management a full trail
    of who did what and when — essential for
    resolving payment disputes or lease issues.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="audit_logs"
    )
    action     = models.CharField(max_length=100)
    details    = models.TextField(blank=True)
    ip_address = models.CharField(
        max_length=45, blank=True
    )
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ["-timestamp"]
        verbose_name        = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return (
            f"[{self.timestamp:%Y-%m-%d %H:%M}] "
            f"{self.user} — {self.action}"
        )
