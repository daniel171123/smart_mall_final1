from django import forms
from .models import Complaint


class ComplaintForm(forms.ModelForm):
    class Meta:
        model  = Complaint
        fields = [
            'complaint_type', 'subject',
            'description', 'invoice', 'payment'
        ]
        widgets = {
            'complaint_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Brief summary of your complaint'
            }),
            'description': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        4,
                'placeholder': 'Describe your complaint in detail...'
            }),
            'invoice': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class ComplaintResponseForm(forms.ModelForm):
    class Meta:
        model  = Complaint
        fields = ['status', 'response', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'response': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
        }