from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from accounts.decorators import role_required
from .models import TenantProfile
from .forms import TenantCreationForm, TenantEditForm, generate_temp_password

User = get_user_model()


@role_required('SUPER_ADMIN', 'MANAGER')
def tenant_list(request):
    tenants = TenantProfile.objects.select_related(
        'user'
    ).all().order_by('business_name')
    return render(request, 'tenants/tenant_list.html',
                  {'tenants': tenants})


@role_required('SUPER_ADMIN', 'MANAGER')
def tenant_create(request):
    form = TenantCreationForm(
        request.POST or None,
        request.FILES or None
    )
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data

        # Step 1: Generate temp password
        temp_password = generate_temp_password()

        # Step 2: Create the user account
        user = User.objects.create_user(
            email        = cd['email'],
            password     = temp_password,
            first_name   = cd['first_name'],
            last_name    = cd['last_name'],
            phone_number = cd.get('phone_number', ''),
            role         = 'TENANT',
            must_change_password = True,
        )

        # Step 3: Create the tenant profile
        TenantProfile.objects.create(
            user                   = user,
            business_name          = cd['business_name'],
            business_type          = cd['business_type'],
            tin_number             = cd.get('tin_number') or None,
            emergency_contact_name = cd.get(
                'emergency_contact_name', ''
            ),
            emergency_contact_phone = cd.get(
                'emergency_contact_phone', ''
            ),
            id_document = request.FILES.get('id_document'),
            created_by  = request.user,
        )

        # Step 4: Send welcome email with credentials
        from notifications.services import (
            send_account_created_notification
        )
        send_account_created_notification(user, temp_password)

        messages.success(
            request,
            f'Tenant account created for {user.get_full_name()}. '
            f'Login credentials sent to {user.email}.'
        )
        return redirect('tenants:tenant_list')

    return render(request, 'tenants/tenant_form.html',
                  {'form': form, 'title': 'Add New Tenant'})


@role_required('SUPER_ADMIN', 'MANAGER')
def tenant_detail(request, pk):
    tenant = get_object_or_404(TenantProfile, pk=pk)
    lease  = tenant.get_active_lease()
    from invoices.models import Invoice
    invoices = Invoice.objects.filter(
        lease__tenant=tenant
    ).order_by('-issue_date')[:10]
    return render(request, 'tenants/tenant_detail.html', {
        'tenant':   tenant,
        'lease':    lease,
        'invoices': invoices,
    })


@role_required('SUPER_ADMIN', 'MANAGER')
def tenant_edit(request, pk):
    tenant = get_object_or_404(TenantProfile, pk=pk)
    form   = TenantEditForm(
        request.POST  or None,
        request.FILES or None,
        instance=tenant
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tenant updated successfully.')
        return redirect('tenants:tenant_detail', pk=pk)
    return render(request, 'tenants/tenant_form.html',
                  {'form': form,
                   'title': 'Edit Tenant',
                   'object': tenant})

@role_required('SUPER_ADMIN', 'MANAGER')
def tenant_delete(request, pk):
    """
    WHY: We don't hard-delete tenants who have
    invoices or payments — that would break financial
    records. Instead we deactivate their account.
    If they have NO financial history, we allow
    full deletion.
    """
    tenant = get_object_or_404(TenantProfile, pk=pk)

    # Check if tenant has any invoices
    from invoices.models import Invoice
    has_invoices = Invoice.objects.filter(
        lease__tenant=tenant
    ).exists()

    if request.method == 'POST':
        if has_invoices:
            # Safe deactivation — keep records intact
            tenant.user.is_active = False
            tenant.user.save(update_fields=['is_active'])
            messages.success(
                request,
                f'{tenant.business_name} has been '
                f'deactivated. Their financial records '
                f'are preserved.'
            )
        else:
            # No financial history — safe to fully delete
            user = tenant.user
            tenant.delete()
            user.delete()
            messages.success(
                request,
                'Tenant deleted successfully.'
            )
        return redirect('tenants:tenant_list')

    return render(request,
                  'tenants/tenant_confirm_delete.html', {
                      'tenant':       tenant,
                      'has_invoices': has_invoices,
                  })