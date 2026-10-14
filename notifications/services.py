from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from .models import Notification


def _send_email(subject, html_message, recipient_email):
    """
    WHY: Central email sender. All emails go through
    here so error handling is consistent everywhere.
    Returns True if sent, False if failed.
    """
    try:
        send_mail(
            subject       = subject,
            message       = '',
            from_email    = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [recipient_email],
            html_message  = html_message,
            fail_silently = False,
        )
        return True
    except Exception as e:
        return str(e)


def _build_invoice_context(invoice):
    """
    WHY: Every notification email about an invoice
    needs the same data. Build it once here.
    """
    today        = timezone.now().date()
    days_overdue = invoice.get_days_overdue()
    days_until   = invoice.get_days_until_due()

    return {
        'invoice':          invoice,
        'tenant':           invoice.lease.tenant,
        'lease':            invoice.lease,
        'shop':             invoice.lease.shop,
        'mall':             invoice.lease.shop.mall,
        'today':            today,
        'days_overdue':     days_overdue,
        'days_until_due':   days_until,
        'base_rent':        invoice.base_rent,
        'maintenance_fee':  invoice.maintenance_fee,
        'penalty_amount':   invoice.penalty_amount,
        'other_charges':    invoice.other_charges,
        'total_amount':     invoice.total_amount,
        'due_date':         invoice.due_date,
        'period_start':     invoice.period_start,
        'period_end':       invoice.period_end,
    }


def _create_and_send(
    recipient,
    invoice,
    notification_type,
    subject,
    template_name
):
    """
    WHY: Shared helper that:
    1. Builds the email HTML
    2. Creates a Notification log record
    3. Sends the email
    4. Updates the log record with result
    """
    context      = _build_invoice_context(invoice)
    html_message = render_to_string(template_name, context)

    notification = Notification.objects.create(
        recipient         = recipient,
        invoice           = invoice,
        notification_type = notification_type,
        channel           = Notification.Channel.EMAIL,
        subject           = subject,
        message           = html_message,
        is_sent           = False,
    )

    result = _send_email(subject, html_message, recipient.email)

    if result is True:
        notification.is_sent = True
        notification.sent_at = timezone.now()
    else:
        notification.error_message = str(result)

    notification.save(update_fields=[
        'is_sent', 'sent_at', 'error_message'
    ])

    return notification


def send_invoice_generated_notification(invoice):
    """New invoice created — inform tenant."""
    tenant    = invoice.lease.tenant
    recipient = tenant.user
    subject   = (
        f'New Invoice — {invoice.invoice_number} | '
        f'Smart Mall System'
    )
    return _create_and_send(
        recipient,
        invoice,
        Notification.NotificationType.PRE_DEADLINE,
        subject,
        'notifications/emails/invoice_generated.html'
    )


def send_pre_deadline_reminder(invoice):
    """
    WHY: Sent 3 days before due date.
    Gives tenant time to pay before penalty starts.
    """
    tenant    = invoice.lease.tenant
    recipient = tenant.user
    subject   = (
        f'Payment Reminder — Due in 3 Days | '
        f'{invoice.invoice_number}'
    )
    return _create_and_send(
        recipient,
        invoice,
        Notification.NotificationType.PRE_DEADLINE,
        subject,
        'notifications/emails/pre_deadline_reminder.html'
    )


def send_post_deadline_reminder(invoice):
    """
    WHY: Sent every 3 days after due date until paid.
    Shows updated penalty so tenant sees real cost
    of continued non-payment.
    """
    tenant    = invoice.lease.tenant
    recipient = tenant.user
    subject   = (
        f'OVERDUE: Invoice {invoice.invoice_number} — '
        f'ETB {invoice.total_amount} Due Now'
    )
    return _create_and_send(
        recipient,
        invoice,
        Notification.NotificationType.POST_DEADLINE,
        subject,
        'notifications/emails/post_deadline_reminder.html'
    )


def send_payment_verified_notification(payment):
    """Sent when finance officer verifies a payment."""
    invoice   = payment.invoice
    tenant    = invoice.lease.tenant
    recipient = tenant.user
    subject   = (
        f'Payment Confirmed — {invoice.invoice_number} | '
        f'Smart Mall System'
    )
    context   = _build_invoice_context(invoice)
    context['payment'] = payment
    html_message = render_to_string(
        'notifications/emails/payment_confirmed.html',
        context
    )
    notification = Notification.objects.create(
        recipient         = recipient,
        invoice           = invoice,
        notification_type = Notification.NotificationType.PAYMENT_CONFIRMED,
        channel           = Notification.Channel.EMAIL,
        subject           = subject,
        message           = html_message,
        is_sent           = False,
    )
    result = _send_email(subject, html_message, recipient.email)
    if result is True:
        notification.is_sent = True
        notification.sent_at = timezone.now()
    else:
        notification.error_message = str(result)
    notification.save(update_fields=[
        'is_sent', 'sent_at', 'error_message'
    ])
    return notification


def send_payment_rejected_notification(payment):
    """Sent when finance officer rejects a payment."""
    invoice   = payment.invoice
    tenant    = invoice.lease.tenant
    recipient = tenant.user
    subject   = (
        f'Payment Rejected — {invoice.invoice_number} | '
        f'Action Required'
    )
    context      = _build_invoice_context(invoice)
    context['payment'] = payment
    html_message = render_to_string(
        'notifications/emails/payment_rejected.html',
        context
    )
    notification = Notification.objects.create(
        recipient         = recipient,
        invoice           = invoice,
        notification_type = Notification.NotificationType.PAYMENT_REJECTED,
        channel           = Notification.Channel.EMAIL,
        subject           = subject,
        message           = html_message,
        is_sent           = False,
    )
    result = _send_email(subject, html_message, recipient.email)
    if result is True:
        notification.is_sent = True
        notification.sent_at = timezone.now()
    else:
        notification.error_message = str(result)
    notification.save(update_fields=[
        'is_sent', 'sent_at', 'error_message'
    ])
    return notification


def send_lease_expiry_warning(lease):
    """Sent 30 days before lease expiry."""
    tenant    = lease.tenant
    recipient = tenant.user
    subject   = (
        f'Lease Expiry Notice — '
        f'{lease.days_until_expiry()} Days Remaining'
    )
    context = {
        'tenant':          tenant,
        'lease':           lease,
        'shop':            lease.shop,
        'mall':            lease.shop.mall,
        'days_remaining':  lease.days_until_expiry(),
        'end_date':        lease.end_date,
    }
    html_message = render_to_string(
        'notifications/emails/lease_expiry_warning.html',
        context
    )
    notification = Notification.objects.create(
        recipient         = recipient,
        notification_type = Notification.NotificationType.LEASE_EXPIRY,
        channel           = Notification.Channel.EMAIL,
        subject           = subject,
        message           = html_message,
        is_sent           = False,
    )
    result = _send_email(subject, html_message, recipient.email)
    if result is True:
        notification.is_sent = True
        notification.sent_at = timezone.now()
    else:
        notification.error_message = str(result)
    notification.save(update_fields=[
        'is_sent', 'sent_at', 'error_message'
    ])
    return notification


def send_account_created_notification(user, raw_password):
    """
    WHY: When manager creates a tenant account,
    the tenant must receive their login credentials
    by email since they cannot self-register.
    """
    subject = 'Your Smart Mall Account Has Been Created'
    context = {
        'user':         user,
        'raw_password': raw_password,
        'login_url':    f'{settings.ALLOWED_HOSTS[0]}'
                        f'/accounts/login/',
    }
    html_message = render_to_string(
        'notifications/emails/account_created.html',
        context
    )
    notification = Notification.objects.create(
        recipient         = user,
        notification_type = Notification.NotificationType.ACCOUNT_CREATED,
        channel           = Notification.Channel.EMAIL,
        subject           = subject,
        message           = html_message,
        is_sent           = False,
    )
    result = _send_email(subject, html_message, user.email)
    if result is True:
        notification.is_sent = True
        notification.sent_at = timezone.now()
    else:
        notification.error_message = str(result)
    notification.save(update_fields=[
        'is_sent', 'sent_at', 'error_message'
    ])
    return notification