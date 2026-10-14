from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_daily_penalty_update(self):
    """
    WHY: Runs every day at midnight.
    Finds all invoices that are past their due date
    and still unpaid. Calculates penalty as:
    1% of monthly rent × days overdue.
    Updates the invoice total and logs each day.
    """
    try:
        from invoices.services import update_invoice_penalties
        count = update_invoice_penalties()
        logger.info(
            f'Penalty update complete: {count} invoices updated'
        )
        return f'Updated penalties on {count} invoices'
    except Exception as exc:
        logger.error(f'Penalty update failed: {exc}')
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def run_quarterly_invoice_generation(self):
    """
    WHY: Runs every day at 00:05.
    Checks all active leases. If today matches the
    start of a new 3-month cycle (based on lease
    start date), generates a new invoice automatically.
    """
    try:
        from invoices.services import (
            generate_quarterly_invoices
        )
        count = generate_quarterly_invoices()
        logger.info(
            f'Invoice generation complete: '
            f'{count} invoices created'
        )
        return f'Generated {count} new invoices'
    except Exception as exc:
        logger.error(
            f'Invoice generation failed: {exc}'
        )
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def run_notification_reminders(self):
    """
    WHY: Runs every day at 9am.

    Pre-deadline: Sends reminder 3 days before due date.
    Shows full breakdown: rent + maintenance + total.

    Post-deadline: Sends reminder every 3 days after
    due date until paid. Shows updated penalty amount
    so tenant sees the real cost of non-payment.
    """
    try:
        from django.utils import timezone
        from django.conf import settings
        from invoices.models import Invoice
        from notifications.services import (
            send_pre_deadline_reminder,
            send_post_deadline_reminder,
        )
        from datetime import timedelta

        today = timezone.now().date()
        sent  = 0

        # ── Pre-deadline reminders ──────────────────
        # Find invoices due exactly 3 days from now
        target_due = today + timedelta(
            days=settings.PRE_DEADLINE_REMINDER_DAYS
        )
        pre_invoices = Invoice.objects.filter(
            status=Invoice.Status.UNPAID,
            due_date=target_due
        ).select_related(
            'lease__tenant__user',
            'lease__shop__mall'
        )
        for invoice in pre_invoices:
            try:
                send_pre_deadline_reminder(invoice)
                sent += 1
                logger.info(
                    f'Pre-deadline reminder sent: '
                    f'{invoice.invoice_number}'
                )
            except Exception as e:
                logger.error(
                    f'Failed to send pre-deadline '
                    f'reminder for '
                    f'{invoice.invoice_number}: {e}'
                )

        # ── Post-deadline reminders ─────────────────
        # Find all overdue invoices
        # Send on day 1, 4, 7, 10... after due date
        interval = (
            settings.POST_DEADLINE_REMINDER_INTERVAL_DAYS
        )
        overdue_invoices = Invoice.objects.filter(
            status=Invoice.Status.OVERDUE
        ).select_related(
            'lease__tenant__user',
            'lease__shop__mall',
            'lease__shop'
        )
        for invoice in overdue_invoices:
            days_overdue = (today - invoice.due_date).days
            # WHY: Send on day 1, then every 3 days
            # days_overdue % interval == 1 catches
            # day 1, 4, 7, 10, 13...
            if days_overdue >= 1 and \
               (days_overdue == 1 or
                    days_overdue % interval == 0):
                try:
                    send_post_deadline_reminder(invoice)
                    sent += 1
                    logger.info(
                        f'Post-deadline reminder sent: '
                        f'{invoice.invoice_number} '
                        f'({days_overdue} days overdue)'
                    )
                except Exception as e:
                    logger.error(
                        f'Failed to send post-deadline '
                        f'reminder for '
                        f'{invoice.invoice_number}: {e}'
                    )

        return f'Sent {sent} reminder notifications'

    except Exception as exc:
        logger.error(
            f'Notification reminders failed: {exc}'
        )
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def run_lease_expiry_warnings(self):
    """
    WHY: Runs every day at 00:10.
    Finds leases expiring in exactly 30 days and
    sends warning emails to both the tenant and
    the mall admin.
    """
    try:
        from django.utils import timezone
        from django.conf import settings
        from leases.models import Lease
        from notifications.services import (
            send_lease_expiry_warning
        )
        from datetime import timedelta

        warning_date = (
            timezone.now().date() +
            timedelta(
                days=settings.LEASE_EXPIRY_WARNING_DAYS
            )
        )
        leases = Lease.objects.filter(
            status='ACTIVE',
            end_date=warning_date
        ).select_related(
            'tenant__user',
            'shop__mall'
        )

        count = 0
        for lease in leases:
            try:
                send_lease_expiry_warning(lease)
                count += 1
                logger.info(
                    f'Lease expiry warning sent: '
                    f'{lease.tenant.business_name}'
                )
            except Exception as e:
                logger.error(
                    f'Failed to send lease expiry '
                    f'warning for '
                    f'{lease.tenant.business_name}: {e}'
                )

        return f'Sent {count} lease expiry warnings'

    except Exception as exc:
        logger.error(
            f'Lease expiry warnings failed: {exc}'
        )
        raise self.retry(exc=exc, countdown=300)
    
@shared_task(bind=True, max_retries=2)
def run_database_backup(self):
    """Weekly automated database backup."""
    try:
        from django.core.management import call_command
        call_command('backup_db')
        return 'Database backup completed'
    except Exception as exc:
        logger.error(f'Database backup failed: {exc}')
        raise self.retry(exc=exc, countdown=600)