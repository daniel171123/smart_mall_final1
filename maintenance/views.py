from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import MaintenanceRequest
from .forms import MaintenanceRequestForm, MaintenanceUpdateForm


@login_required
def request_list(request):
    """
    WHY: Finance officers do not handle physical
    maintenance. They only see the list if needed
    but cannot update status.
    MANAGER/SUPER_ADMIN: full access.
    FINANCE: no access to maintenance.
    """
    if request.user.role == 'FINANCE':
        messages.error(
            request,
            'Finance officers do not have access '
            'to maintenance requests.'
        )
        return redirect('dashboard:home')

    if not request.user.is_staff_member:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    status   = request.GET.get('status', '')
    requests = MaintenanceRequest.objects.select_related(
        'shop__mall', 'requested_by', 'assigned_to'
    ).all()

    if status:
        requests = requests.filter(
            status=status.upper()
        )

    return render(
        request,
        'maintenance/request_list.html', {
            'requests':        requests,
            'selected_status': status,
        }
    )


@role_required('SUPER_ADMIN', 'MANAGER')
def request_detail(request, pk):
    req  = get_object_or_404(MaintenanceRequest, pk=pk)
    form = MaintenanceUpdateForm(
        request.POST or None, instance=req
    )
    if request.method == 'POST' and form.is_valid():
        r = form.save(commit=False)
        if r.status == 'COMPLETED' and not r.completed_at:
            r.completed_at = timezone.now()
        r.save()
        messages.success(
            request,
            'Maintenance request updated.'
        )
        return redirect('maintenance:request_detail', pk=pk)
    return render(request,
                  'maintenance/request_detail.html', {
                      'req':  req,
                      'form': form,
                  })


@login_required
def my_requests(request):
    requests = MaintenanceRequest.objects.filter(
        requested_by=request.user
    ).order_by('-created_at')
    return render(request,
                  'maintenance/my_requests.html',
                  {'requests': requests})


@login_required
def request_create(request):
    form = MaintenanceRequestForm(request.POST or None)

    # Limit shops to tenant's own shop
    if request.user.role == 'TENANT':
        try:
            lease = request.user.tenant_profile\
                        .get_active_lease()
            if lease:
                from malls.models import Shop
                form.fields['shop'].queryset = (
                    Shop.objects.filter(
                        pk=lease.shop.pk
                    )
                )
        except Exception:
            pass

    if request.method == 'POST' and form.is_valid():
        req              = form.save(commit=False)
        req.requested_by = request.user
        req.save()
        messages.success(
            request,
            'Maintenance request submitted.'
        )
        if request.user.role == 'TENANT':
            return redirect('maintenance:my_requests')
        return redirect('maintenance:request_list')

    return render(request,
                  'maintenance/request_form.html',
                  {'form':  form,
                   'title': 'New Maintenance Request'})