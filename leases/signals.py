from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lease


@receiver(post_save, sender=Lease)
def on_lease_created(sender, instance, created, **kwargs):
    """
    WHY: When a new lease is saved for the first time,
    automatically generate the first invoice.
    We use post_save with 'created=True' so this
    only fires on creation, not on every update.
    """
    if created and instance.status == 'ACTIVE':
        from invoices.services import generate_invoice_for_lease
        from notifications.services import (
            send_invoice_generated_notification
        )
        invoice = generate_invoice_for_lease(
            instance,
            period_start=instance.start_date
        )
        if invoice:
            send_invoice_generated_notification(invoice)