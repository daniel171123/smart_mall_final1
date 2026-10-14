from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import role_required
from .models import Mall, Shop
from .forms import MallForm, ShopForm


@role_required('SUPER_ADMIN', 'MANAGER')
def mall_list(request):
    malls = Mall.objects.all()
    return render(request, 'malls/mall_list.html',
                  {'malls': malls})


@role_required('SUPER_ADMIN')
def mall_create(request):
    form = MallForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Mall created successfully.')
        return redirect('malls:mall_list')
    return render(request, 'malls/mall_form.html',
                  {'form': form, 'title': 'Add New Mall'})


@role_required('SUPER_ADMIN')
def mall_edit(request, pk):
    mall = get_object_or_404(Mall, pk=pk)
    form = MallForm(request.POST or None, instance=mall)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Mall updated successfully.')
        return redirect('malls:mall_list')
    return render(request, 'malls/mall_form.html',
                  {'form': form, 'title': 'Edit Mall',
                   'object': mall})


@role_required('SUPER_ADMIN', 'MANAGER')
def shop_list(request):
    mall_id = request.GET.get('mall')
    status  = request.GET.get('status')
    shops   = Shop.objects.select_related('mall').all()
    malls   = Mall.objects.all()
    if mall_id:
        shops = shops.filter(mall_id=mall_id)
    if status:
        shops = shops.filter(status=status)
    return render(request, 'malls/shop_list.html', {
        'shops': shops,
        'malls': malls,
        'selected_mall':   mall_id,
        'selected_status': status,
    })


@role_required('SUPER_ADMIN', 'MANAGER')
def shop_create(request):
    form = ShopForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Shop created successfully.')
        return redirect('malls:shop_list')
    return render(request, 'malls/shop_form.html',
                  {'form': form, 'title': 'Add New Shop'})


@role_required('SUPER_ADMIN', 'MANAGER')
def shop_edit(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    form = ShopForm(request.POST or None, instance=shop)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Shop updated successfully.')
        return redirect('malls:shop_list')
    return render(request, 'malls/shop_form.html',
                  {'form': form, 'title': 'Edit Shop',
                   'object': shop})
@role_required('SUPER_ADMIN')
def mall_delete(request, pk):
    mall = get_object_or_404(Mall, pk=pk)
    has_shops = mall.shops.exists()

    if request.method == 'POST':
        if has_shops:
            messages.error(
                request,
                f'Cannot delete {mall.name} — it still '
                f'has {mall.shops.count()} shop(s). '
                f'Remove all shops first.'
            )
            return redirect('malls:mall_list')
        mall_name = mall.name
        mall.delete()
        messages.success(
            request,
            f'Mall "{mall_name}" deleted successfully.'
        )
        return redirect('malls:mall_list')

    return render(
        request,
        'malls/mall_confirm_delete.html',
        {'mall': mall, 'has_shops': has_shops}
    )


@role_required('SUPER_ADMIN', 'MANAGER')
def shop_delete(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    has_leases = shop.leases.filter(
        status='ACTIVE'
    ).exists()

    if request.method == 'POST':
        if has_leases:
            messages.error(
                request,
                f'Cannot delete Shop {shop.shop_number}'
                f' — it has an active lease.'
            )
            return redirect('malls:shop_list')
        shop.delete()
        messages.success(
            request,
            f'Shop {shop.shop_number} deleted.'
        )
        return redirect('malls:shop_list')

    return render(
        request,
        'malls/shop_confirm_delete.html',
        {'shop': shop, 'has_leases': has_leases}
    )