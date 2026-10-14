from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from .models import Invoice
from .forms import ManualInvoiceForm
from decimal import Decimal


@role_required('SUPER_ADMIN', 'MANAGER', 'FINANCE')
def invoice_list(request):
    status   = request.GET.get('status', '')
    invoices = Invoice.objects.select_related(
        'lease__tenant__user',
        'lease__shop__mall'
    ).all()
    if status:
        invoices = invoices.filter(status=status.upper())
    return render(request, 'invoices/invoice_list.html', {
        'invoices':        invoices,
        'selected_status': status,
    })


@role_required('SUPER_ADMIN', 'MANAGER', 'FINANCE')
def invoice_detail(request, pk):
    invoice  = get_object_or_404(
        Invoice.objects.select_related(
            'lease__tenant__user',
            'lease__shop__mall'
        ), pk=pk
    )
    logs = invoice.penalty_logs.order_by('-date')[:10]
    try:
        payment = invoice.payment
    except Exception:
        payment = None
    return render(request, 'invoices/invoice_detail.html', {
        'invoice': invoice,
        'logs':    logs,
        'payment': payment,
    })


@role_required('SUPER_ADMIN', 'MANAGER')
def invoice_create(request):
    form = ManualInvoiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        invoice = form.save(commit=False)
        invoice.invoice_number = Invoice.generate_invoice_number()
        invoice.issue_date     = timezone.now().date()
        invoice.total_amount   = (
            invoice.base_rent +
            invoice.maintenance_fee +
            invoice.other_charges
        )
        invoice.generated_automatically = False
        invoice.save()
        messages.success(
            request,
            f'Invoice {invoice.invoice_number} created.'
        )
        return redirect('invoices:invoice_detail',
                        pk=invoice.pk)
    return render(request, 'invoices/invoice_form.html',
                  {'form': form,
                   'title': 'Create Manual Invoice'})


@login_required
def my_invoices(request):
    try:
        tenant    = request.user.tenant_profile
        lease     = tenant.get_active_lease()
        invoices_qs = Invoice.objects.filter(
            lease=lease
        ).order_by('-issue_date') if lease else []

        invoices = []
        for inv in invoices_qs:
            try:
                pay = inv.payment
                inv.payment_status   = pay.status
                inv.rejection_reason = pay.rejection_reason
            except Exception:
                inv.payment_status   = None
                inv.rejection_reason = None
            invoices.append(inv)

    except Exception:
        invoices = []
        lease    = None

    return render(
        request,
        'invoices/my_invoices.html',
        {
            'invoices': invoices,
            'lease':    lease,
        }
    )

@role_required('SUPER_ADMIN', 'MANAGER')
def invoice_delete(request, pk):
    """
    WHY: Allows admin/manager to delete a manually
    created invoice that was made by mistake.
    Only UNPAID invoices with no payment submission
    can be deleted.
    Auto-generated invoices can also be deleted if
    they have no associated payment.
    """
    from django.shortcuts import get_object_or_404
    invoice = get_object_or_404(Invoice, pk=pk)

    # Cannot delete paid invoices
    if invoice.status == Invoice.Status.PAID:
        messages.error(
            request,
            "Cannot delete a paid invoice. "
            "Paid invoices are permanent financial records."
        )
        return redirect(
            "invoices:invoice_detail", pk=pk
        )

    # Cannot delete if payment proof has been submitted
    try:
        if invoice.payment:
            messages.error(
                request,
                "Cannot delete this invoice — a payment "
                "submission exists. Reject the payment "
                "first, then delete."
            )
            return redirect(
                "invoices:invoice_detail", pk=pk
            )
    except Exception:
        pass

    if request.method == "POST":
        invoice_number = invoice.invoice_number
        invoice.delete()

        try:
            from accounts.audit import audit_log
            audit_log(
                user=request.user,
                action="INVOICE_DELETED",
                details=f"Invoice {invoice_number} deleted",
                request=request,
            )
        except Exception:
            pass

        messages.success(
            request,
            f"Invoice {invoice_number} deleted."
        )
        return redirect("invoices:invoice_list")

    return render(
        request,
        "invoices/invoice_confirm_delete.html",
        {"invoice": invoice},
    )
