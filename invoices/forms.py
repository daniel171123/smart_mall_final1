from django import forms
from .models import Invoice


class ManualInvoiceForm(forms.ModelForm):
    """
    WHY: For one-off invoices created manually
    by admin/manager outside the quarterly cycle.
    """
    class Meta:
        model  = Invoice
        fields = [
            'lease', 'period_start', 'period_end',
            'base_rent', 'maintenance_fee',
            'other_charges', 'other_charges_description',
            'due_date'
        ]
        widgets = {
            'lease': forms.Select(attrs={
                'class': 'form-select'
            }),
            'period_start': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'period_end': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'base_rent': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'maintenance_fee': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'other_charges': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'other_charges_description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
        }