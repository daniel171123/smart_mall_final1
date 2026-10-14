from django import forms
from .models import MaintenanceRequest


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model  = MaintenanceRequest
        fields = ['shop', 'title', 'description', 'priority']
        widgets = {
            'shop': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Brief title of the issue'
            }),
            'description': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        4,
                'placeholder': 'Describe the maintenance issue in detail...'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class MaintenanceUpdateForm(forms.ModelForm):
    class Meta:
        model  = MaintenanceRequest
        fields = ['status', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
        }