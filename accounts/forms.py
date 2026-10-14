
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()


def validate_phone(value):
    if not value:
        return
    cleaned = re.sub(r"[\s\-]", "", value)
    if not re.match(r"^\+?\d{7,15}$", cleaned):
        raise ValidationError(
            "Enter a valid phone number. "
            "Only digits, +, spaces, and hyphens. "
            "Example: +251911234567"
        )


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            "class":       "form-control form-control-lg",
            "placeholder": "Enter your email address",
            "autofocus":   True,
        }),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class":       "form-control form-control-lg",
            "placeholder": "Enter your password",
        }),
    )
    error_messages = {
        "invalid_login": (
            "Invalid email or password. Please try again."
        ),
        "inactive": "This account has been deactivated.",
    }


class ForcePasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Temporary Password",
        widget=forms.PasswordInput(attrs={
            "class":       "form-control",
            "placeholder": "Enter your temporary password",
        }),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "class":       "form-control",
            "placeholder": "Choose a strong new password",
        }),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            "class":       "form-control",
            "placeholder": "Repeat your new password",
        }),
    )


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            "class":       "form-control form-control-lg",
            "placeholder": "Enter your registered email",
        }),
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "class":       "form-control",
            "placeholder": "Enter new password",
        }),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            "class":       "form-control",
            "placeholder": "Repeat new password",
        }),
    )


class StaffCreationForm(forms.Form):
    """
    Staff account creation form.
    Admin can either set a specific password or
    leave it blank to auto-generate one.
    """
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "First name",
        }),
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Last name",
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "staff@smartmall.com",
        }),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        validators=[validate_phone],
        widget=forms.TextInput(attrs={
            "class":       "form-control",
            "placeholder": "+251911234567",
            "pattern":     r"[\+\d\s\-]{7,20}",
            "title":       "Phone: digits, +, spaces, hyphens only",
        }),
    )
    role = forms.ChoiceField(
        choices=[
            ("MANAGER",     "Manager"),
            ("FINANCE",     "Finance Officer"),
            ("SUPER_ADMIN", "Super Admin"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    mall = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="— Super Admin (All Malls) —",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text=(
            "Assign to a specific mall. "
            "Leave blank for Super Admin."
        ),
    )
    # WHY: Optional password field. If left blank,
    # system auto-generates a secure temp password.
    # If filled, the admin sets a known password —
    # user still must change it on first login.
    set_password = forms.CharField(
        label="Set Password (optional)",
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            "class":       "form-control",
            "placeholder": "Leave blank to auto-generate",
        }),
        help_text=(
            "If left blank, a secure password will be "
            "generated and emailed to the user. "
            "User must change it on first login."
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        required=False,
        widget=forms.PasswordInput(attrs={
            "class":       "form-control",
            "placeholder": "Repeat password if set above",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from malls.models import Mall
        self.fields["mall"].queryset = Mall.objects.all()

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "A user with this email already exists."
            )
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("set_password", "")
        p2 = cleaned.get("confirm_password", "")
        if p1 and p1 != p2:
            raise forms.ValidationError(
                "Passwords do not match."
            )
        return cleaned


class UserEditForm(forms.ModelForm):
    class Meta:
        model  = get_user_model()
        fields = [
            "first_name", "last_name",
            "phone_number", "role", "is_active",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "phone_number": forms.TextInput(attrs={
                "class":       "form-control",
                "placeholder": "+251911234567",
            }),
            "role": forms.Select(attrs={
                "class": "form-select"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone_number"].validators.append(
            validate_phone
        )
