from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    WHY: Every email/SMS sent is logged here.
    This gives admins full visibility into what
    was sent, when, and whether it succeeded.
    Also prevents duplicate sends — we can check
    if a notification was already sent before sending.
    """

    class NotificationType(models.TextChoices):
        PRE_DEADLINE       = 'PRE_DEADLINE',       'Pre-Deadline Reminder'
        POST_DEADLINE      = 'POST_DEADLINE',       'Post-Deadline Reminder'
        LEASE_EXPIRY       = 'LEASE_EXPIRY',        'Lease Expiry Warning'
        PAYMENT_CONFIRMED  = 'PAYMENT_CONFIRMED',   'Payment Confirmed'
        PAYMENT_REJECTED   = 'PAYMENT_REJECTED',    'Payment Rejected'
        ACCOUNT_CREATED    = 'ACCOUNT_CREATED',     'Account Created'
        GENERAL            = 'GENERAL',             'General Notice'

    class Channel(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SMS   = 'SMS',   'SMS'
        BOTH  = 'BOTH',  'Email & SMS'

    recipient         = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                            related_name='notifications'
                        )
    # WHY: Nullable — some notifications are not invoice-related
    invoice           = models.ForeignKey(
                            'invoices.Invoice',
                            on_delete=models.SET_NULL,
                            null=True,
                            blank=True,
                            related_name='notifications'
                        )
    notification_type = models.CharField(
                            max_length=30,
                            choices=NotificationType.choices
                        )
    channel           = models.CharField(
                            max_length=10,
                            choices=Channel.choices,
                            default=Channel.EMAIL
                        )
    subject           = models.CharField(max_length=200)
    message           = models.TextField()
    is_sent           = models.BooleanField(default=False)
    sent_at           = models.DateTimeField(null=True, blank=True)
    error_message     = models.TextField(
                            blank=True,
                            help_text='Populated if sending failed'
                        )
    created_at        = models.DateTimeField(auto_now_add=True)
    
    seen = models.BooleanField(default=False)
    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return (
            f'{self.notification_type} → '
            f'{self.recipient.email} '
            f'({"Sent" if self.is_sent else "Pending"})'
        )