from django import forms
from django.contrib.auth import get_user_model
from .models import TenantProfile
import random
import string
import re
from django.core.exceptions import ValidationError

User = get_user_model()


def generate_temp_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def validate_phone(value):
    if not value:
        return
    cleaned = re.sub(r'[\s\-]', '', value)
    if not re.match(r'^\+?\d{7,15}$', cleaned):
        raise ValidationError(
            'Enter a valid phone number. '
            'Only digits, +, spaces, and hyphens. '
            'Example: +251911234567'
        )


class TenantCreationForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Last name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class':       'form-control',
            'placeholder': 'tenant@email.com'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        validators=[validate_phone],
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': '+251911234567',
            'pattern':     r'[\+\d\s\-]{7,20}',
            'title':       'Phone: digits, +, spaces, hyphens only'
        })
    )
    business_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Business / shop name'
        })
    )
    business_type = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'e.g. Clothing, Electronics'
        })
    )
    tin_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Tax Identification Number'
        })
    )
    emergency_contact_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    emergency_contact_phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[validate_phone],
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': '+251911234567',
            'pattern':     r'[\+\d\s\-]{7,20}',
            'title':       'Phone: digits, +, spaces, hyphens only'
        })
    )
    id_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'A user with this email already exists.'
            )
        return email
    
    def clean_tin_number(self):
        tin = self.cleaned_data.get('tin_number', '').strip()
        if not tin:
            return tin
        from tenants.models import TenantProfile
        if TenantProfile.objects.filter(
            tin_number=tin
        ).exists():
            raise forms.ValidationError(
            f'A tenant with TIN number "{tin}" already '
            f'exists. Please verify and enter a unique TIN.'
        )
        return tin


class TenantEditForm(forms.ModelForm):
    class Meta:
        model  = TenantProfile
        fields = [
            'business_name', 'business_type',
            'tin_number',
            'emergency_contact_name',
            'emergency_contact_phone',
            'id_document'
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'business_type': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'tin_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': '+251911234567',
                'pattern':     r'[\+\d\s\-]{7,20}',
                'title':       'Phone: digits, +, spaces, hyphens only'
            }),
            'id_document': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['emergency_contact_phone'].validators.append(
            validate_phone
        )