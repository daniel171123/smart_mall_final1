from django import forms
from django.core.exceptions import ValidationError
from .models import Lease
from tenants.models import TenantProfile
from malls.models import Shop


class LeaseForm(forms.ModelForm):
    class Meta:
        model  = Lease
        fields = [
            'shop', 'tenant', 'monthly_rent',
            'maintenance_fee', 'security_deposit',
            'start_date', 'end_date',
            'payment_due_days', 'lease_document'
        ]
        widgets = {
            'shop': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tenant': forms.Select(attrs={
                'class': 'form-select'
            }),
            'monthly_rent': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monthly rent in ETB',
                'min': '1',
                'step': '0.01'
            }),
            'maintenance_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quarterly maintenance fee in ETB',
                'min': '0',
                'step': '0.01'
            }),
            'security_deposit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Security deposit in ETB',
                'min': '0',
                'step': '0.01'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date'
            }),
            'payment_due_days': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'lease_document': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # WHY: Only show vacant shops in the dropdown
        # when creating a new lease
        if not self.instance.pk:
            self.fields['shop'].queryset = (
                Shop.objects.filter(status='VACANT')
                    .select_related('mall')
            )

    def clean(self):
        cleaned = super().clean()
        start   = cleaned.get('start_date')
        end     = cleaned.get('end_date')
        shop    = cleaned.get('shop')

        if start and end and end <= start:
            raise ValidationError(
                'End date must be after start date.'
            )

        # Business rule: no two active leases for same shop
        if shop and not self.instance.pk:
            if Lease.objects.filter(
                shop=shop, status='ACTIVE'
            ).exists():
                raise ValidationError(
                    f'Shop {shop.shop_number} already '
                    f'has an active lease.'
                )
        return cleaned


class LeaseTerminateForm(forms.Form):
    termination_reason = forms.CharField(
        label='Reason for Termination',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows':  3,
            'placeholder': 'Explain why this lease is being terminated...'
        })
    )