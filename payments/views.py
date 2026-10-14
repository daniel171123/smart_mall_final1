from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Payment
from .forms import SubmitPaymentForm, VerifyPaymentForm
from invoices.models import Invoice


@role_required("SUPER_ADMIN", "MANAGER", "FINANCE")
def payment_list(request):
    status   = request.GET.get("status", "")
    payments = Payment.objects.select_related(
        "tenant__user", "invoice"
    ).all()
    if status:
        payments = payments.filter(status=status)
    return render(
        request,
        "payments/payment_list.html",
        {"payments": payments, "selected_status": status},
    )


@login_required
def my_payments(request):
    try:
        tenant   = request.user.tenant_profile
        payments = Payment.objects.filter(
            tenant=tenant
        ).select_related("invoice").order_by(
            "-submitted_at"
        )
    except Exception:
        payments = []
    return render(
        request,
        "payments/my_payments.html",
        {"payments": payments},
    )


@login_required
def submit_payment(request, inv_pk):
    invoice = get_object_or_404(Invoice, pk=inv_pk)

    try:
        tenant = request.user.tenant_profile
    except Exception:
        messages.error(
            request, "Only tenants can submit payments."
        )
        return redirect("dashboard:home")

    if invoice.lease.tenant != tenant:
        messages.error(
            request, "You can only pay your own invoices."
        )
        return redirect("invoices:my_invoices")

    if invoice.status == Invoice.Status.PAID:
        messages.error(
            request, "This invoice is already paid."
        )
        return redirect("invoices:my_invoices")

    existing = Payment.objects.filter(
        invoice=invoice
    ).first()

    if existing:
        if existing.status == "PENDING_VERIFICATION":
            messages.warning(
                request,
                "You already submitted payment for this "
                "invoice. Please wait for verification.",
            )
            return redirect("invoices:my_invoices")
        elif existing.status == "REJECTED":
            existing.delete()
            messages.info(
                request,
                "Your previous rejected payment has been "
                "cleared. Please submit a new payment.",
            )

    initial = {"amount_paid": invoice.total_amount}
    form    = SubmitPaymentForm(
        request.POST  or None,
        request.FILES or None,
        initial=initial,
    )

    if request.method == "POST" and form.is_valid():
        payment         = form.save(commit=False)
        payment.invoice = invoice
        payment.tenant  = tenant
        payment.status  = "PENDING_VERIFICATION"
        payment.save()
        _notify_finance_new_payment(payment)
        messages.success(
            request,
            "Payment submitted successfully. "
            "Awaiting finance verification.",
        )
        return redirect("invoices:my_invoices")

    return render(
        request,
        "payments/submit_payment.html",
        {"form": form, "invoice": invoice},
    )


def _notify_finance_new_payment(payment):
    from django.contrib.auth import get_user_model
    from notifications.models import Notification
    from django.core.mail import send_mail
    from django.conf import settings

    User = get_user_model()
    recipients = list(User.objects.filter(
        role="FINANCE", is_active=True
    )) + list(User.objects.filter(
        role__in=["MANAGER", "SUPER_ADMIN"],
        is_active=True
    ))

    inv_num  = payment.invoice.invoice_number
    biz      = payment.tenant.business_name
    amt      = str(payment.amount_paid)
    method   = payment.get_payment_method_display()
    subject  = "New Payment Submitted — " + inv_num + " | " + biz
    body     = (
        "Tenant " + biz + " submitted payment proof "
        "for invoice " + inv_num + ". "
        "Amount: ETB " + amt + ". "
        "Method: " + method + ". "
        "Please verify in the Payments section."
    )

    for user in recipients:
        Notification.objects.create(
            recipient         = user,
            invoice           = payment.invoice,
            notification_type = "GENERAL",
            channel           = "EMAIL",
            subject           = subject,
            message           = body,
            is_sent           = True,
            sent_at           = timezone.now(),
        )
        try:
            send_mail(
                subject        = subject,
                message        = body,
                from_email     = settings.DEFAULT_FROM_EMAIL,
                recipient_list = [user.email],
                fail_silently  = True,
            )
        except Exception:
            pass


@role_required("FINANCE")
def verify_payment(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related(
            "invoice__lease__tenant__user",
            "invoice__lease__shop__mall",
            "tenant__user",
        ),
        pk=pk,
        status="PENDING_VERIFICATION",
    )
    form = VerifyPaymentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        action = form.cleaned_data["action"]

        if action == "verify":
            payment.status      = "VERIFIED"
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()

            payment.invoice.status = Invoice.Status.PAID
            payment.invoice.save(update_fields=["status"])

            try:
                from notifications.services import (
                    send_payment_verified_notification,
                )
                send_payment_verified_notification(payment)
            except Exception:
                pass

            _send_receipt_email(payment)

            try:
                from accounts.audit import audit_log
                audit_log(
                    user    = request.user,
                    action  = "PAYMENT_VERIFIED",
                    details = (
                        "Invoice "
                        + payment.invoice.invoice_number
                        + " — ETB "
                        + str(payment.amount_paid)
                    ),
                    request = request,
                )
            except Exception:
                pass

            messages.success(
                request,
                "Payment verified. Invoice "
                + payment.invoice.invoice_number
                + " marked as PAID. Receipt sent.",
            )

        elif action == "reject":
            payment.status           = "REJECTED"
            payment.rejection_reason = (
                form.cleaned_data["rejection_reason"]
            )
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()

            try:
                from notifications.services import (
                    send_payment_rejected_notification,
                )
                send_payment_rejected_notification(payment)
            except Exception:
                pass

            try:
                from accounts.audit import audit_log
                audit_log(
                    user    = request.user,
                    action  = "PAYMENT_REJECTED",
                    details = (
                        "Invoice "
                        + payment.invoice.invoice_number
                        + " — Reason: "
                        + payment.rejection_reason
                    ),
                    request = request,
                )
            except Exception:
                pass

            messages.warning(
                request,
                "Payment rejected. Tenant notified.",
            )

        return redirect("payments:payment_list")

    return render(
        request,
        "payments/verify_payment.html",
        {"payment": payment, "form": form},
    )


def _send_receipt_email(payment):
    try:
        from .receipt import generate_receipt_pdf
        from django.core.mail import EmailMessage
        from django.conf import settings

        buf      = generate_receipt_pdf(payment)
        inv_num  = payment.invoice.invoice_number
        filename = "Receipt_" + inv_num + ".pdf"
        subject  = "Payment Receipt — " + inv_num
        tenant   = payment.tenant.user.get_full_name()
        mall     = payment.invoice.lease.shop.mall.name
        receipt  = "RCP-" + str(payment.pk).zfill(6)
        amount   = str(payment.amount_paid)

        lines = [
            "Dear " + tenant + ",",
            "",
            "Please find your payment receipt attached.",
            "",
            "Invoice: " + inv_num,
            "Amount:  ETB " + amount,
            "Receipt: " + receipt,
            "",
            "Thank you,",
            mall,
        ]
        body = "\n".join(lines)

        em = EmailMessage(
            subject    = subject,
            body       = body,
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [payment.tenant.user.email],
        )
        em.attach(filename, buf.read(), "application/pdf")
        em.send(fail_silently=True)
    except Exception:
        pass