from django.utils import timezone
from django.conf import settings
from django.db import transaction
from dateutil.relativedelta import relativedelta
from decimal import Decimal


def generate_invoice_for_lease(lease, period_start=None):
    """
    WHY: Central function for creating one invoice
    for one lease. Called in two situations:
    1. Immediately when a new lease is created
    2. By the quarterly Celery scheduler

    Uses a database transaction so if anything fails,
    no partial invoice is saved.
    """
    from .models import Invoice

    # Default: start from lease start date
    if period_start is None:
        period_start = lease.start_date

    period_end = period_start + relativedelta(months=3) \
                 - relativedelta(days=1)
    issue_date = period_start
    due_date   = issue_date + relativedelta(
                     days=lease.payment_due_days
                 )

    # WHY: Check if invoice already exists for this
    # period to prevent duplicates
    existing = Invoice.objects.filter(
        lease=lease,
        period_start=period_start,
    ).first()

    if existing:
        return existing

    base_rent       = lease.monthly_rent * 3
    maintenance_fee = lease.maintenance_fee
    total_amount    = base_rent + maintenance_fee

    with transaction.atomic():
        invoice = Invoice.objects.create(
            lease           = lease,
            invoice_number  = Invoice.generate_invoice_number(),
            period_start    = period_start,
            period_end      = period_end,
            base_rent       = base_rent,
            maintenance_fee = maintenance_fee,
            penalty_amount  = Decimal('0.00'),
            other_charges   = Decimal('0.00'),
            total_amount    = total_amount,
            issue_date      = issue_date,
            due_date        = due_date,
            status          = Invoice.Status.UNPAID,
            generated_automatically = True,
        )

    return invoice


def generate_quarterly_invoices():
    """
    WHY: Called by Celery Beat every day.
    Checks all active leases and generates the next
    quarterly invoice if it is due today.

    Logic:
    - Start from lease.start_date
    - Add 3 months repeatedly until we reach today
    - If today matches a cycle start date → generate
    """
    from leases.models import Lease

    today  = timezone.now().date()
    leases = Lease.objects.filter(status='ACTIVE')
    count  = 0

    for lease in leases:
        cycle_date = lease.start_date

        # Walk forward in 3-month steps
        while cycle_date <= today:
            if cycle_date == today:
                invoice = generate_invoice_for_lease(
                    lease,
                    period_start=cycle_date
                )
                if invoice:
                    count += 1
                    # Send invoice notification
                    from notifications.services import (
                        send_invoice_generated_notification
                    )
                    send_invoice_generated_notification(invoice)
                break
            cycle_date += relativedelta(months=3)

    return count


def update_invoice_penalties():
    """
    WHY: Called daily by Celery Beat.
    For every overdue unpaid invoice:
    1. Calculate how many days past due
    2. Calculate penalty = days × 1% × monthly_rent
    3. Update invoice total
    4. Log the penalty entry
    5. Update invoice status to OVERDUE
    """
    from .models import Invoice, PenaltyLog
    from decimal import Decimal

    today    = timezone.now().date()
    invoices = Invoice.objects.filter(
        status__in=[
            Invoice.Status.UNPAID,
            Invoice.Status.OVERDUE
        ],
        due_date__lt=today
    )

    for invoice in invoices:
        days_overdue    = (today - invoice.due_date).days
        daily_rate      = invoice.lease.monthly_rent * \
                          Decimal(str(settings.PENALTY_RATE_PER_DAY))
        total_penalty   = daily_rate * days_overdue

        # Update invoice
        invoice.penalty_amount = total_penalty
        invoice.total_amount   = (
            invoice.base_rent +
            invoice.maintenance_fee +
            invoice.penalty_amount +
            invoice.other_charges
        )
        invoice.status = Invoice.Status.OVERDUE
        invoice.save(update_fields=[
            'penalty_amount',
            'total_amount',
            'status'
        ])

        # Log daily entry — unique_together prevents duplicates
        PenaltyLog.objects.get_or_create(
            invoice            = invoice,
            date               = today,
            defaults={
                'days_overdue':       days_overdue,
                'daily_penalty_rate': daily_rate,
                'cumulative_penalty': total_penalty,
            }
        )

    return invoices.count()