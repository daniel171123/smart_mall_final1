from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import role_required
from .models import Lease
from .forms import LeaseForm, LeaseTerminateForm


@role_required('SUPER_ADMIN', 'MANAGER')
def lease_list(request):
    status = request.GET.get('status', '')
    leases = Lease.objects.select_related(
        'tenant__user', 'shop__mall'
    ).all()
    if status == 'expiring':
        from datetime import timedelta
        leases = leases.filter(
            status='ACTIVE',
            end_date__lte=(
                timezone.now().date() + timedelta(days=30)
            )
        )
    elif status:
        leases = leases.filter(status=status.upper())
    return render(request, 'leases/lease_list.html', {
        'leases':          leases,
        'selected_status': status,
    })


@role_required('SUPER_ADMIN', 'MANAGER')
def lease_create(request):
    form = LeaseForm(
        request.POST or None,
        request.FILES or None
    )
    if request.method == 'POST' and form.is_valid():
        lease            = form.save(commit=False)
        lease.created_by = request.user
        lease.status     = 'ACTIVE'
        lease.save()
        messages.success(
            request,
            'Lease created. First invoice generated automatically.'
        )
        return redirect('leases:lease_detail', pk=lease.pk)
    return render(request, 'leases/lease_form.html', {
        'form':  form,
        'title': 'Create New Lease'
    })


@role_required('SUPER_ADMIN', 'MANAGER')
def lease_detail(request, pk):
    lease = get_object_or_404(
        Lease.objects.select_related(
            'tenant__user', 'shop__mall', 'created_by'
        ),
        pk=pk
    )
    invoices = lease.invoices.order_by('-issue_date')
    return render(request, 'leases/lease_detail.html', {
        'lease':    lease,
        'invoices': invoices,
    })


@role_required('SUPER_ADMIN', 'MANAGER')
def lease_terminate(request, pk):
    lease = get_object_or_404(
        Lease, pk=pk, status='ACTIVE'
    )
    form = LeaseTerminateForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        lease.status             = 'TERMINATED'
        lease.terminated_at      = timezone.now()
        lease.termination_reason = (
            form.cleaned_data['termination_reason']
        )
        lease.save()

        # Audit log
        try:
            from accounts.audit import audit_log
            audit_log(
                user=request.user,
                action='LEASE_TERMINATED',
                details=(
                    f'Lease for '
                    f'{lease.tenant.business_name} — '
                    f'Shop {lease.shop.shop_number} — '
                    f'Reason: {lease.termination_reason}'
                ),
                request=request,
            )
        except Exception:
            pass

        messages.success(
            request,
            'Lease terminated. Shop marked as vacant.'
        )
        return redirect('leases:lease_list')

    return render(
        request,
        'leases/lease_terminate.html',
        {'lease': lease, 'form': form}
    )