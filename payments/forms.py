from django import forms
from django.core.exceptions import ValidationError
from .models import Payment


class SubmitPaymentForm(forms.ModelForm):
    """
    WHY: Tenant submits this form to upload proof.
    The amount_paid is pre-filled from the invoice
    and made read-only — tenant cannot change it.
    """
    class Meta:
        model  = Payment
        fields = [
            'amount_paid', 'payment_date',
            'payment_method', 'transaction_reference',
            'proof_of_payment'
        ]
        widgets = {
            'amount_paid': forms.NumberInput(attrs={
                'class':    'form-control',
                'readonly': True,
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'transaction_reference': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Bank ref or Telebirr ID'
            }),
            'proof_of_payment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


class VerifyPaymentForm(forms.Form):
    """
    WHY: Finance officer uses this to approve
    or reject a payment submission.
    """
    ACTION_CHOICES = [
        ('verify', 'Verify — Mark as Paid'),
        ('reject', 'Reject — Send Back to Tenant'),
    ]
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class':       'form-control',
            'rows':        3,
            'placeholder': 'Required if rejecting. '
                           'Explain clearly so tenant can resubmit.'
        })
    )

    def clean(self):
        cleaned = super().clean()
        action  = cleaned.get('action')
        reason  = cleaned.get('rejection_reason', '').strip()
        if action == 'reject' and not reason:
            raise ValidationError(
                'You must provide a reason when rejecting a payment.'
            )
        return cleaned