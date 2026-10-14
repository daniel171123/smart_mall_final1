from django.db import models
from django.conf import settings


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING_VERIFICATION = 'PENDING_VERIFICATION', \
                               'Pending Verification'
        VERIFIED             = 'VERIFIED',   'Verified'
        REJECTED             = 'REJECTED',   'Rejected'

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        TELEBIRR      = 'TELEBIRR',      'Telebirr'
        CASH          = 'CASH',          'Cash'
        CHEQUE        = 'CHEQUE',        'Cheque'

    # WHY: OneToOne — strictly one payment per invoice
    invoice = models.OneToOneField(
        'invoices.Invoice',
        on_delete=models.PROTECT,
        related_name='payment'
    )
    tenant = models.ForeignKey(
        'tenants.TenantProfile',
        on_delete=models.PROTECT,
        related_name='payments'
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    payment_date = models.DateField(
        help_text='Date tenant claims to have paid'
    )
    proof_of_payment = models.FileField(
        upload_to='payment_proofs/',
        help_text='Required — image or PDF'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices
    )
    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text='Bank ref or Telebirr transaction ID'
    )
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.PENDING_VERIFICATION
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    # WHY: SET_NULL so payment record survives if
    # the finance officer account is deleted
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )
    verified_at      = models.DateTimeField(
        null=True, blank=True
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text='Required if payment is rejected'
    )

    class Meta:
        ordering     = ['-submitted_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return (
            f'Payment for '
            f'{self.invoice.invoice_number} — '
            f'{self.tenant.business_name} '
            f'({self.status})'
        )