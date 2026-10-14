from django.db import models
from django.conf import settings


class StaffProfile(models.Model):
    """
    WHY: Separates staff-specific fields from the
    core CustomUser model. Keeps accounts app clean
    and focused only on authentication.
    """
    user          = models.OneToOneField(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                        related_name='staff_profile'
                    )
    mall          = models.ForeignKey(
                        'malls.Mall',
                        on_delete=models.SET_NULL,
                        null=True,
                        blank=True,
                        related_name='staff_members'
                    )
    employee_id   = models.CharField(max_length=50, unique=True)
    department    = models.CharField(max_length=100, blank=True)
    date_employed = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'

    def __str__(self):
        return f'{self.user.get_full_name()} — {self.user.role}'


class TenantProfile(models.Model):
    """
    WHY: Holds all business-related info about a tenant.
    Separated from CustomUser so the auth layer stays clean.
    The OneToOneField means one user = one tenant profile.
    """
    user                  = models.OneToOneField(
                                settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='tenant_profile'
                            )
    business_name         = models.CharField(max_length=200)
    business_type         = models.CharField(max_length=100)
    tin_number            = models.CharField(
                                max_length=50,
                                unique=True,
                                blank=True,
                                null=True
                            )
    emergency_contact_name  = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    id_document           = models.FileField(
                                upload_to='tenant_documents/ids/',
                                blank=True,
                                null=True
                            )
    # WHY: Track which manager created this account
    # SET_NULL so if manager leaves, tenant record stays
    created_by            = models.ForeignKey(
                                settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                related_name='created_tenants'
                            )
    created_at            = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tenant Profile'
        verbose_name_plural = 'Tenant Profiles'
        ordering = ['business_name']

    def __str__(self):
        return (
            f'{self.business_name} '
            f'({self.user.get_full_name()})'
        )

    def get_active_lease(self):
        return self.leases.filter(status='ACTIVE').first()

    def get_unpaid_invoices(self):
        from invoices.models import Invoice
        active_lease = self.get_active_lease()
        if not active_lease:
            return Invoice.objects.none()
        return active_lease.invoices.filter(
            status__in=['UNPAID', 'OVERDUE']
        )

    def get_total_outstanding(self):
        return sum(
            inv.total_amount
            for inv in self.get_unpaid_invoices()
        )