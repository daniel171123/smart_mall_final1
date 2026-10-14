from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Lease(models.Model):
    """
    WHY: The Lease is the contract between the mall and
    a tenant for a specific shop. It drives everything —
    invoice generation is based on lease start date and
    monthly rent. Without an active lease, no invoices
    are generated.
    """

    class Status(models.TextChoices):
        ACTIVE     = 'ACTIVE',     'Active'
        EXPIRED    = 'EXPIRED',    'Expired'
        TERMINATED = 'TERMINATED', 'Terminated'

    shop             = models.ForeignKey(
                           'malls.Shop',
                           on_delete=models.PROTECT,
                           related_name='leases'
                       )
    tenant           = models.ForeignKey(
                           'tenants.TenantProfile',
                           on_delete=models.PROTECT,
                           related_name='leases'
                       )
    monthly_rent     = models.DecimalField(max_digits=10, decimal_places=2)
    maintenance_fee  = models.DecimalField(
                           max_digits=10,
                           decimal_places=2,
                           help_text='Fixed fee charged per quarter'
                       )
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    start_date       = models.DateField()
    end_date         = models.DateField()
    status           = models.CharField(
                           max_length=20,
                           choices=Status.choices,
                           default=Status.ACTIVE
                       )
    lease_document   = models.FileField(
                           upload_to='lease_documents/',
                           blank=True,
                           null=True
                       )
    # WHY: Stored on lease so it can differ per tenant
    # if needed in the future
    payment_due_days = models.IntegerField(
                           default=10,
                           help_text='Days tenant has to pay after invoice is generated'
                       )
    created_by       = models.ForeignKey(
                           settings.AUTH_USER_MODEL,
                           on_delete=models.SET_NULL,
                           null=True,
                           related_name='created_leases'
                       )
    created_at       = models.DateTimeField(auto_now_add=True)
    terminated_at    = models.DateTimeField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)

    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'Lease'
        verbose_name_plural = 'Leases'

    def __str__(self):
        return (
            f'Lease: {self.tenant.business_name} — '
            f'Shop {self.shop.shop_number} '
            f'({self.status})'
        )

    def clean(self):
        """
        WHY: Enforce business rule — a shop cannot have
        two active leases at the same time.
        This runs on both admin saves and form saves.
        """
        from django.core.exceptions import ValidationError
        if self.status == 'ACTIVE':
            existing = Lease.objects.filter(
                shop=self.shop,
                status='ACTIVE'
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    f'Shop {self.shop.shop_number} already '
                    f'has an active lease.'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # WHY: Automatically update shop status
        # when lease status changes
        if self.status == 'ACTIVE':
            self.shop.status = 'OCCUPIED'
        else:
            # Check if any other active lease exists
            other_active = Lease.objects.filter(
                shop=self.shop,
                status='ACTIVE'
            ).exclude(pk=self.pk).exists()
            if not other_active:
                self.shop.status = 'VACANT'
        self.shop.save(update_fields=['status'])

    # ── Helper Methods ─────────────────────────────────────────────

    def get_quarterly_base_rent(self):
        """Monthly rent × 3"""
        return self.monthly_rent * 3

    def get_quarterly_invoice_base_total(self):
        """Base rent + maintenance fee for one quarter"""
        return self.get_quarterly_base_rent() + self.maintenance_fee

    def get_next_invoice_date(self):
        """
        WHY: Invoices follow Option B — cycle starts
        from lease start date. This calculates the
        next invoice generation date based on how
        many quarters have passed.
        """
        from dateutil.relativedelta import relativedelta
        today = timezone.now().date()
        invoice_date = self.start_date
        while invoice_date <= today:
            invoice_date += relativedelta(months=3)
        return invoice_date - relativedelta(months=3)

    def is_expiring_soon(self):
        """True if lease expires within 30 days"""
        days_left = (self.end_date - timezone.now().date()).days
        return 0 < days_left <= 30

    def days_until_expiry(self):
        return (self.end_date - timezone.now().date()).days