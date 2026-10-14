from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = (
        'Run all daily scheduled tasks manually. '
        'Useful for testing without waiting for '
        'Celery Beat schedule.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            default='all',
            help=(
                'Which task to run: '
                'penalties | invoices | reminders | '
                'expiry | all'
            )
        )

    def handle(self, *args, **options):
        task = options['task']
        self.stdout.write(
            f'\n[{timezone.now().strftime("%Y-%m-%d %H:%M")}] '
            f'Running task: {task}\n'
        )

        if task in ('penalties', 'all'):
            self.stdout.write('Running penalty update...')
            from invoices.services import (
                update_invoice_penalties
            )
            count = update_invoice_penalties()
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Penalties updated on {count} invoices'
                )
            )

        if task in ('invoices', 'all'):
            self.stdout.write(
                'Running quarterly invoice generation...'
            )
            from invoices.services import (
                generate_quarterly_invoices
            )
            count = generate_quarterly_invoices()
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Generated {count} new invoices'
                )
            )

        if task in ('reminders', 'all'):
            self.stdout.write(
                'Running notification reminders...'
            )
            from django.utils import timezone as tz
            from django.conf import settings
            from invoices.models import Invoice
            from notifications.services import (
                send_pre_deadline_reminder,
                send_post_deadline_reminder,
            )
            from datetime import timedelta

            today = tz.now().date()
            sent  = 0

            target_due = today + timedelta(
                days=settings.PRE_DEADLINE_REMINDER_DAYS
            )
            for inv in Invoice.objects.filter(
                status=Invoice.Status.UNPAID,
                due_date=target_due
            ):
                send_pre_deadline_reminder(inv)
                sent += 1

            interval = (
                settings.POST_DEADLINE_REMINDER_INTERVAL_DAYS
            )
            for inv in Invoice.objects.filter(
                status=Invoice.Status.OVERDUE
            ):
                days = (today - inv.due_date).days
                if days >= 1 and (
                    days == 1 or days % interval == 0
                ):
                    send_post_deadline_reminder(inv)
                    sent += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'  Sent {sent} reminder notifications'
                )
            )

        if task in ('expiry', 'all'):
            self.stdout.write(
                'Running lease expiry warnings...'
            )
            from leases.models import Lease
            from notifications.services import (
                send_lease_expiry_warning
            )
            from django.conf import settings
            from datetime import timedelta

            warning_date = (
                timezone.now().date() +
                timedelta(
                    days=settings.LEASE_EXPIRY_WARNING_DAYS
                )
            )
            count = 0
            for lease in Lease.objects.filter(
                status='ACTIVE',
                end_date=warning_date
            ):
                send_lease_expiry_warning(lease)
                count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'  Sent {count} lease expiry warnings'
                )
            )

        self.stdout.write(
            self.style.SUCCESS('\nAll tasks completed.\n')
        )