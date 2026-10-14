from celery import shared_task


@shared_task
def run_daily_penalty_update():
    """
    WHY: Runs every day at midnight.
    Updates penalty on all overdue invoices.
    """
    from .services import update_invoice_penalties
    count = update_invoice_penalties()
    return f'Updated penalties on {count} invoices'


@shared_task
def run_quarterly_invoice_generation():
    """
    WHY: Runs every day at midnight.
    Generates new invoices for leases whose
    quarterly cycle starts today.
    """
    from .services import generate_quarterly_invoices
    count = generate_quarterly_invoices()
    return f'Generated {count} new invoices'


@shared_task
def run_notification_reminders():
    """
    WHY: Runs every day at 9am.
    Sends pre-deadline reminders (3 days before due)
    and post-deadline reminders (every 3 days after).
    """
    from django.utils import timezone
    from django.conf import settings
    from .models import Invoice
    from notifications.services import (
        send_pre_deadline_reminder,
        send_post_deadline_reminder,
    )

    today = timezone.now().date()
    sent  = 0

    # Pre-deadline: 3 days before due date
    pre_deadline_invoices = Invoice.objects.filter(
        status=Invoice.Status.UNPAID,
        due_date=today + __import__(
            'datetime'
        ).timedelta(
            days=settings.PRE_DEADLINE_REMINDER_DAYS
        )
    )
    for invoice in pre_deadline_invoices:
        send_pre_deadline_reminder(invoice)
        sent += 1

    # Post-deadline: every 3 days after due date
    overdue_invoices = Invoice.objects.filter(
        status=Invoice.Status.OVERDUE
    )
    interval = settings.POST_DEADLINE_REMINDER_INTERVAL_DAYS

    for invoice in overdue_invoices:
        days_overdue = (today - invoice.due_date).days
        # WHY: Send on day 1, 4, 7, 10... etc
        if days_overdue > 0 and days_overdue % interval == 0:
            send_post_deadline_reminder(invoice)
            sent += 1

    return f'Sent {sent} reminder notifications'


@shared_task
def run_lease_expiry_warnings():
    """
    WHY: Runs every day. Sends warning to tenants
    whose lease expires in exactly 30 days.
    """
    from django.utils import timezone
    from django.conf import settings
    from leases.models import Lease
    from notifications.services import send_lease_expiry_warning
    from datetime import timedelta

    warning_date = (
        timezone.now().date() +
        timedelta(days=settings.LEASE_EXPIRY_WARNING_DAYS)
    )
    leases = Lease.objects.filter(
        status='ACTIVE',
        end_date=warning_date
    )
    for lease in leases:
        send_lease_expiry_warning(lease)

    return f'Sent {leases.count()} lease expiry warnings'