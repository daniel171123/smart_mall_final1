import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'core.settings'
)

app = Celery('core')
app.config_from_object(
    'django.conf:settings',
    namespace='CELERY'
)
app.autodiscover_tasks()


# ── Scheduled Tasks ────────────────────────────────────────────────
# WHY: We define the schedule here so it is always
# registered when Celery starts, regardless of whether
# django-celery-beat has run yet.

app.conf.beat_schedule = {

    # ── Midnight Tasks ─────────────────────────────
    'update-penalties-daily': {
        'task':     'invoices.tasks.run_daily_penalty_update',
        'schedule': crontab(hour=0, minute=0),
        # Runs every day at 00:00 (midnight)
    },
    'generate-quarterly-invoices-daily': {
        'task':     (
            'invoices.tasks'
            '.run_quarterly_invoice_generation'
        ),
        'schedule': crontab(hour=0, minute=5),
        # Runs every day at 00:05
        # WHY: 5 minutes after penalty update so
        # new invoices start clean
    },
    'lease-expiry-warnings-daily': {
        'task':     'invoices.tasks.run_lease_expiry_warnings',
        'schedule': crontab(hour=0, minute=10),
        # Runs every day at 00:10
    },

    # ── Morning Reminder Task ───────────────────────
    'send-reminder-notifications-daily': {
        'task':     'invoices.tasks.run_notification_reminders',
        'schedule': crontab(hour=9, minute=0),
        # Runs every day at 09:00am Ethiopian time
    },
    'weekly-database-backup': {
    'task':     'invoices.tasks.run_database_backup',
    'schedule': crontab(
        hour=2, minute=0,
        day_of_week='sunday'
    ),
    # Every Sunday at 2am
},
}

app.conf.timezone = 'Africa/Addis_Ababa'