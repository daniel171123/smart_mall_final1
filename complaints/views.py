from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Complaint
from .forms import ComplaintForm, ComplaintResponseForm


@login_required
def complaint_list(request):
    """
    WHY: Staff see complaints based on their role.
    - SUPER_ADMIN/MANAGER: see all complaints
    - FINANCE: only sees INVOICE_DISPUTE and
      PAYMENT_ISSUE complaints
    """
    if not request.user.is_staff_member:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    status     = request.GET.get('status', '')
    complaints = Complaint.objects.select_related(
        'tenant__user', 'assigned_to'
    ).all()

    # Finance sees only finance-related complaints
    if request.user.role == 'FINANCE':
        complaints = complaints.filter(
            complaint_type__in=[
                'INVOICE_DISPUTE',
                'PAYMENT_ISSUE'
            ]
        )

    if status:
        complaints = complaints.filter(
            status=status.upper()
        )

    return render(
        request,
        'complaints/complaint_list.html', {
            'complaints':      complaints,
            'selected_status': status,
        }
    )


@role_required('SUPER_ADMIN', 'MANAGER', 'FINANCE')
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    form      = ComplaintResponseForm(
        request.POST or None,
        instance=complaint
    )
    if request.method == 'POST' and form.is_valid():
        c = form.save(commit=False)
        if c.status == 'RESOLVED' and not c.resolved_at:
            c.resolved_at = timezone.now()
        c.save()
        messages.success(request,
                         'Complaint updated successfully.')
        return redirect('complaints:complaint_detail', pk=pk)
    return render(request, 'complaints/complaint_detail.html', {
        'complaint': complaint,
        'form':      form,
    })


@login_required
def my_complaints(request):
    try:
        tenant     = request.user.tenant_profile
        complaints = Complaint.objects.filter(
            tenant=tenant
        ).order_by('-created_at')
    except Exception:
        complaints = []
        tenant     = None
    return render(request,
                  'complaints/my_complaints.html', {
                      'complaints': complaints,
                      'tenant':     tenant,
                  })


@login_required
def complaint_create(request):
    try:
        tenant = request.user.tenant_profile
    except Exception:
        messages.error(
            request,
            'Only tenants can submit complaints.'
        )
        return redirect('dashboard:home')

    form = ComplaintForm(request.POST or None)

    # Limit invoice/payment choices to tenant's own
    from invoices.models import Invoice
    from payments.models import Payment
    lease = tenant.get_active_lease()
    form.fields['invoice'].queryset = (
        Invoice.objects.filter(lease=lease)
        if lease else Invoice.objects.none()
    )
    form.fields['invoice'].required = False
    form.fields['payment'].queryset = (
        Payment.objects.filter(tenant=tenant)
    )
    form.fields['payment'].required = False

    if request.method == 'POST' and form.is_valid():
        complaint        = form.save(commit=False)
        complaint.tenant = tenant
        complaint.status = 'OPEN'
        complaint.save()
        messages.success(
            request,
            'Complaint submitted successfully.'
        )
        return redirect('complaints:my_complaints')

    return render(request, 'complaints/complaint_form.html',
                  {'form': form,
                   'title': 'Submit a Complaint'})