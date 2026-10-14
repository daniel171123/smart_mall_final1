from django.db import models
from django.utils import timezone
from django.conf import settings


class Invoice(models.Model):
    """
    WHY: Invoices are the financial core of the system.
    They are generated automatically every quarter per
    active lease. total_amount is NOT static — it is
    recalculated daily as penalty accumulates.
    """

    class Status(models.TextChoices):
        UNPAID  = 'UNPAID',  'Unpaid'
        PAID    = 'PAID',    'Paid'
        OVERDUE = 'OVERDUE', 'Overdue'

    lease          = models.ForeignKey(
                         'leases.Lease',
                         on_delete=models.PROTECT,
                         related_name='invoices'
                     )
    invoice_number = models.CharField(max_length=50, unique=True)
    period_start   = models.DateField()
    period_end     = models.DateField()

    # ── Amount Breakdown ───────────────────────────────────────────
    base_rent      = models.DecimalField(
                         max_digits=10,
                         decimal_places=2,
                         help_text='monthly_rent × 3'
                     )
    maintenance_fee = models.DecimalField(
                          max_digits=10,
                          decimal_places=2
                      )
    penalty_amount  = models.DecimalField(
                          max_digits=10,
                          decimal_places=2,
                          default=0
                      )
    other_charges   = models.DecimalField(
                          max_digits=10,
                          decimal_places=2,
                          default=0
                      )
    other_charges_description = models.TextField(blank=True)

    # WHY: Stored separately so we can always show
    # the breakdown without recalculating
    total_amount    = models.DecimalField(
                          max_digits=10,
                          decimal_places=2
                      )

    # ── Dates ──────────────────────────────────────────────────────
    issue_date = models.DateField(default=timezone.now)
    due_date   = models.DateField()

    # ── Status ─────────────────────────────────────────────────────
    status = models.CharField(
                 max_length=10,
                 choices=Status.choices,
                 default=Status.UNPAID
             )
    generated_automatically = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ['-issue_date']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return (
            f'{self.invoice_number} — '
            f'{self.lease.tenant.business_name} '
            f'({self.status})'
        )

    def recalculate_total(self):
        """
        WHY: Called daily by Celery task.
        Keeps total_amount always accurate including
        the latest penalty.
        """
        self.total_amount = (
            self.base_rent +
            self.maintenance_fee +
            self.penalty_amount +
            self.other_charges
        )
        self.save(update_fields=['total_amount'])

    def calculate_current_penalty(self):
        """
        WHY: 1% of monthly rent per day overdue.
        Only calculated if invoice is past due date
        and still unpaid.
        """
        if self.status == self.Status.PAID:
            return self.penalty_amount
        today = timezone.now().date()
        if today <= self.due_date:
            return 0
        days_overdue     = (today - self.due_date).days
        daily_rate       = self.lease.monthly_rent * \
                           settings.PENALTY_RATE_PER_DAY
        return round(daily_rate * days_overdue, 2)

    def get_days_overdue(self):
        if self.status == self.Status.PAID:
            return 0
        today = timezone.now().date()
        if today <= self.due_date:
            return 0
        return (today - self.due_date).days

    def get_days_until_due(self):
        today = timezone.now().date()
        delta = (self.due_date - today).days
        return delta if delta >= 0 else 0

    def is_overdue(self):
        return (
            timezone.now().date() > self.due_date
            and self.status != self.Status.PAID
        )

    @classmethod
    def generate_invoice_number(cls):
        """
        WHY: Generates sequential invoice numbers like
        INV-2026-00001. Uses DB count to ensure uniqueness.
        """
        year  = timezone.now().year
        count = cls.objects.filter(
            issue_date__year=year
        ).count() + 1
        return f'INV-{year}-{count:05d}'


class PenaltyLog(models.Model):
    """
    WHY: Full audit trail of how penalty grew day by day.
    Essential for transparency — tenant can see exactly
    why their total increased and by how much each day.
    """
    invoice            = models.ForeignKey(
                             Invoice,
                             on_delete=models.CASCADE,
                             related_name='penalty_logs'
                         )
    date               = models.DateField()
    days_overdue       = models.IntegerField()
    daily_penalty_rate = models.DecimalField(
                             max_digits=8,
                             decimal_places=2
                         )
    cumulative_penalty = models.DecimalField(
                             max_digits=10,
                             decimal_places=2
                         )

    class Meta:
        ordering        = ['invoice', 'date']
        # WHY: Only one log entry per invoice per day
        unique_together = ('invoice', 'date')
        verbose_name    = 'Penalty Log'
        verbose_name_plural = 'Penalty Logs'

    def __str__(self):
        return (
            f'{self.invoice.invoice_number} — '
            f'{self.date} — '
            f'{self.days_overdue} days overdue — '
            f'ETB {self.cumulative_penalty}'
        )