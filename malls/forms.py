from django import forms
from django.core.validators import RegexValidator
from .models import Mall, Shop

# WHY: Defined at module level so it can be reused
# across multiple form fields
phone_validator = RegexValidator(
    regex=r'^\+?\d[\d\s\-]{6,19}$',
    message=(
        'Enter a valid phone number. '
        'Only digits, +, spaces, and hyphens allowed. '
        'Example: +251911234567'
    )
)


class MallForm(forms.ModelForm):
    class Meta:
        model  = Mall
        fields = [
            'name', 'location', 'city',
            'contact_phone', 'contact_email'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Friendship Mall'
            }),
            'location': forms.Textarea(attrs={
                'class': 'form-control',
                'rows':  2,
                'placeholder': 'Physical address'
            }),
            'city': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Addis Ababa'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': '+251911234567',
                'pattern':     r'[\+\d\s\-]{7,20}',
                'title': (
                    'Phone: digits, +, spaces, '
                    'hyphens only'
                )
            }),
            'contact_email': forms.EmailInput(attrs={
                'class':       'form-control',
                'placeholder': 'contact@mall.com'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add phone validator to contact_phone field
        self.fields['contact_phone'].validators.append(
            phone_validator
        )


class ShopForm(forms.ModelForm):
    class Meta:
        model  = Shop
        fields = [
            'mall', 'shop_number', 'floor',
            'size_sqm', 'shop_type', 'status',
            'description'
        ]
        widgets = {
            'mall': forms.Select(attrs={
                'class': 'form-select'
            }),
            'shop_number': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. A-101'
            }),
            'floor': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Ground, 1st, 2nd'
            }),
            'size_sqm': forms.NumberInput(attrs={
                'class':       'form-control',
                'placeholder': 'Size in square meters',
                'min':         '1',
                'step':        '0.01'
            }),
            'shop_type': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Retail, Food Court'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows':  2
            }),
        }