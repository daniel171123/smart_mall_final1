from django.db import models
from django.conf import settings


class Complaint(models.Model):

    class ComplaintType(models.TextChoices):
        INVOICE_DISPUTE = 'INVOICE_DISPUTE', 'Invoice Dispute'
        PAYMENT_ISSUE   = 'PAYMENT_ISSUE',   'Payment Issue'
        MAINTENANCE     = 'MAINTENANCE',     'Maintenance'
        GENERAL         = 'GENERAL',         'General'

    class Status(models.TextChoices):
        OPEN        = 'OPEN',        'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED    = 'RESOLVED',    'Resolved'
        CLOSED      = 'CLOSED',      'Closed'

    tenant         = models.ForeignKey(
                         'tenants.TenantProfile',
                         on_delete=models.CASCADE,
                         related_name='complaints'
                     )
    complaint_type = models.CharField(
                         max_length=20,
                         choices=ComplaintType.choices
                     )
    # WHY: Both nullable — complaint may relate to
    # an invoice, a payment, or neither (general)
    invoice        = models.ForeignKey(
                         'invoices.Invoice',
                         on_delete=models.SET_NULL,
                         null=True,
                         blank=True,
                         related_name='complaints'
                     )
    payment        = models.ForeignKey(
                         'payments.Payment',
                         on_delete=models.SET_NULL,
                         null=True,
                         blank=True,
                         related_name='complaints'
                     )
    subject        = models.CharField(max_length=200)
    description    = models.TextField()
    status         = models.CharField(
                         max_length=15,
                         choices=Status.choices,
                         default=Status.OPEN
                     )
    # WHY: SET_NULL so complaint stays if staff leaves
    assigned_to    = models.ForeignKey(
                         settings.AUTH_USER_MODEL,
                         on_delete=models.SET_NULL,
                         null=True,
                         blank=True,
                         related_name='assigned_complaints'
                     )
    response       = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    resolved_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'

    def __str__(self):
        return (
            f'{self.complaint_type} — '
            f'{self.tenant.business_name} '
            f'({self.status})'
        )