
from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.contrib.auth import (
    login, logout, update_session_auth_hash
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetCompleteView,
)
from django.core.cache import cache
from django.urls import reverse_lazy
from .forms import (
    EmailLoginForm,
    ForcePasswordChangeForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
)


# ── Login ──────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    # Rate limiting — 5 attempts per IP per 15 min
    ip = (
        request.META.get("HTTP_X_FORWARDED_FOR", "")
                   .split(",")[0].strip()
        or request.META.get("REMOTE_ADDR", "")
    )
    cache_key    = f"login_attempts_{ip}"
    attempts     = cache.get(cache_key, 0)
    MAX_ATTEMPTS = 5
    LOCKOUT_SECS = 900

    if attempts >= MAX_ATTEMPTS:
        messages.error(
            request,
            "Too many failed login attempts. "
            "Please try again in 15 minutes."
        )
        return render(
            request,
            "accounts/login.html",
            {"form": EmailLoginForm(), "locked": True}
        )

    form = EmailLoginForm(
        request, data=request.POST or None
    )

    if request.method == "POST":
        if form.is_valid():
            cache.delete(cache_key)
            user = form.get_user()
            login(request, user)
            if user.must_change_password:
                messages.warning(
                    request,
                    "Welcome! Please change your "
                    "temporary password before continuing."
                )
                return redirect("accounts:change_password")
            messages.success(
                request,
                f"Welcome back, {user.get_full_name()}!"
            )
            next_url = request.GET.get("next")
            return redirect(next_url or "dashboard:home")
        else:
            cache.set(
                cache_key, attempts + 1, LOCKOUT_SECS
            )
            remaining = MAX_ATTEMPTS - attempts - 1
            if remaining > 0:
                messages.error(
                    request,
                    f"Invalid email or password. "
                    f"{remaining} attempt(s) remaining."
                )
            else:
                messages.error(
                    request,
                    "Account locked for 15 minutes due to "
                    "too many failed attempts."
                )

    return render(
        request, "accounts/login.html", {"form": form}
    )


# ── Logout ─────────────────────────────────────────────────────────
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(
            request, "You have been logged out."
        )
    return redirect("accounts:login")


# ── Change Password ────────────────────────────────────────────────
@login_required
def change_password_view(request):
    form = ForcePasswordChangeForm(
        request.user, request.POST or None
    )
    if request.method == "POST" and form.is_valid():
        user = form.save()
        if user.must_change_password:
            user.must_change_password = False
            user.save(
                update_fields=["must_change_password"]
            )
        update_session_auth_hash(request, user)

        # Audit log
        try:
            from accounts.audit import audit_log
            audit_log(
                user=user,
                action="PASSWORD_CHANGED",
                details="User changed their own password",
                request=request,
            )
        except Exception:
            pass

        messages.success(
            request,
            "Your password has been changed successfully."
        )
        return redirect("dashboard:home")
    elif request.method == "POST":
        messages.error(
            request, "Please correct the errors below."
        )

    return render(
        request,
        "accounts/change_password.html",
        {
            "form":      form,
            "is_forced": request.user.must_change_password,
        },
    )


# ── Change Email ───────────────────────────────────────────────────
@login_required
def change_email(request):
    from django import forms as django_forms

    class ChangeEmailForm(django_forms.Form):
        new_email = django_forms.EmailField(
            widget=django_forms.EmailInput(attrs={
                "class":       "form-control",
                "placeholder": "Enter new email address",
            })
        )
        password = django_forms.CharField(
            label="Confirm Your Password",
            widget=django_forms.PasswordInput(attrs={
                "class":       "form-control",
                "placeholder": "Enter your current password",
            })
        )

        def __init__(self, user, *args, **kwargs):
            self.user = user
            super().__init__(*args, **kwargs)

        def clean_new_email(self):
            from django.contrib.auth import get_user_model
            email = self.cleaned_data["new_email"]
            User  = get_user_model()
            if User.objects.filter(
                email=email
            ).exclude(pk=self.user.pk).exists():
                raise django_forms.ValidationError(
                    "This email is already in use."
                )
            return email

        def clean_password(self):
            pw = self.cleaned_data["password"]
            if not self.user.check_password(pw):
                raise django_forms.ValidationError(
                    "Incorrect password."
                )
            return pw

    form = ChangeEmailForm(
        request.user, request.POST or None
    )
    if request.method == "POST" and form.is_valid():
        old_email = request.user.email
        request.user.email = form.cleaned_data["new_email"]
        request.user.save(update_fields=["email"])

        try:
            from accounts.audit import audit_log
            audit_log(
                user=request.user,
                action="EMAIL_CHANGED",
                details=f"Changed from {old_email}",
                request=request,
            )
        except Exception:
            pass

        messages.success(
            request,
            f"Email changed to {request.user.email}."
        )
        return redirect("dashboard:home")

    return render(
        request,
        "accounts/change_email.html",
        {"form": form},
    )


# ── Password Reset Views ───────────────────────────────────────────
class CustomPasswordResetView(PasswordResetView):
    form_class            = CustomPasswordResetForm
    template_name         = "accounts/forgot_password.html"
    email_template_name   = (
        "accounts/emails/password_reset_email.html"
    )
    subject_template_name = (
        "accounts/emails/password_reset_subject.txt"
    )
    success_url = reverse_lazy(
        "accounts:password_reset_done"
    )


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(
    PasswordResetConfirmView
):
    form_class    = CustomSetPasswordForm
    template_name = "accounts/reset_password.html"
    success_url   = reverse_lazy(
        "accounts:password_reset_complete"
    )


class CustomPasswordResetCompleteView(
    PasswordResetCompleteView
):
    template_name = (
        "accounts/password_reset_complete.html"
    )


# ── User Management ────────────────────────────────────────────────
from accounts.decorators import role_required


@role_required("SUPER_ADMIN")
def user_list(request):
    from django.contrib.auth import get_user_model
    User  = get_user_model()
    users = User.objects.all().order_by(
        "role", "first_name"
    )
    return render(
        request,
        "accounts/user_list.html",
        {"users": users},
    )


@role_required("SUPER_ADMIN")
def user_create(request):
    from .forms import StaffCreationForm
    from django.contrib.auth import get_user_model
    import random, string

    form = StaffCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        User = get_user_model()
        cd   = form.cleaned_data
        # Use admin-set password or auto-generate
        set_pw = cd.get("set_password", "").strip()
        temp   = set_pw if set_pw else "".join(
            random.choices(
                string.ascii_letters + string.digits, k=10
            )
        )
        new_user = User.objects.create_user(
            email        = cd["email"],
            password     = temp,
            first_name   = cd["first_name"],
            last_name    = cd["last_name"],
            phone_number = cd.get("phone_number", ""),
            role         = cd["role"],
            must_change_password = True,
        )
        from tenants.models import StaffProfile
        StaffProfile.objects.create(
            user        = new_user,
            mall        = cd.get("mall"),
            employee_id = f"EMP-{new_user.pk:04d}",
        )
        from notifications.services import (
            send_account_created_notification
        )
        send_account_created_notification(new_user, temp)

        try:
            from accounts.audit import audit_log
            audit_log(
                user=request.user,
                action="USER_CREATED",
                details=(
                    f"Created {cd['role']} account "
                    f"for {cd['email']}"
                ),
                request=request,
            )
        except Exception:
            pass

        messages.success(
            request,
            f"Account created for "
            f"{new_user.get_full_name()}. "
            f"Credentials sent to {new_user.email}."
        )
        return redirect("accounts:user_list")

    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "title": "Add New Staff User"},
    )


@role_required("SUPER_ADMIN")
def user_edit(request, pk):
    from django.contrib.auth import get_user_model
    from .forms import UserEditForm
    User = get_user_model()
    user = get_object_or_404(User, pk=pk)
    form = UserEditForm(
        request.POST or None, instance=user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request, "User updated successfully."
        )
        return redirect("accounts:user_list")
    return render(
        request,
        "accounts/user_form.html",
        {
            "form":   form,
            "title":  f"Edit {user.get_full_name()}",
            "object": user,
        },
    )


@role_required("SUPER_ADMIN")
def user_toggle_active(request, pk):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(
            request,
            "You cannot deactivate your own account."
        )
        return redirect("accounts:user_list")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    status = "activated" if user.is_active else "deactivated"
    messages.success(
        request,
        f"{user.get_full_name()} has been {status}."
    )
    return redirect("accounts:user_list")


@role_required("SUPER_ADMIN")
def user_delete(request, pk):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(
            request,
            "You cannot delete your own account."
        )
        return redirect("accounts:user_list")
    has_records = False
    if user.role == "TENANT":
        try:
            from invoices.models import Invoice
            has_records = Invoice.objects.filter(
                lease__tenant=user.tenant_profile
            ).exists()
        except Exception:
            pass
    if request.method == "POST":
        if has_records:
            user.is_active = False
            user.save(update_fields=["is_active"])
            messages.success(
                request,
                f"{user.get_full_name()} deactivated. "
                "Financial records preserved."
            )
        else:
            name = user.get_full_name()
            user.delete()
            messages.success(
                request,
                f'User "{name}" deleted permanently.'
            )
        return redirect("accounts:user_list")
    return render(
        request,
        "accounts/user_confirm_delete.html",
        {"target_user": user, "has_records": has_records},
    )


@role_required("SUPER_ADMIN", "MANAGER")
def set_user_password(request, pk):
    from django.contrib.auth import get_user_model
    from django import forms as django_forms
    User = get_user_model()
    target_user = get_object_or_404(User, pk=pk)

    class SetPasswordForm(django_forms.Form):
        new_password = django_forms.CharField(
            label="New Password",
            min_length=8,
            widget=django_forms.PasswordInput(attrs={
                "class":       "form-control",
                "placeholder": "Min 8 characters",
            })
        )
        confirm_password = django_forms.CharField(
            label="Confirm Password",
            widget=django_forms.PasswordInput(attrs={
                "class":       "form-control",
                "placeholder": "Repeat the password",
            })
        )

        def clean(self):
            cd = super().clean()
            p1 = cd.get("new_password")
            p2 = cd.get("confirm_password")
            if p1 and p2 and p1 != p2:
                raise django_forms.ValidationError(
                    "Passwords do not match."
                )
            return cd

    form = SetPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        target_user.set_password(
            form.cleaned_data["new_password"]
        )
        target_user.must_change_password = True
        target_user.save()

        try:
            from accounts.audit import audit_log
            audit_log(
                user=request.user,
                action="PASSWORD_SET_BY_ADMIN",
                details=(
                    f"Password set for "
                    f"{target_user.email}"
                ),
                request=request,
            )
        except Exception:
            pass

        messages.success(
            request,
            f"Password set for "
            f"{target_user.get_full_name()}. "
            "They must change it on next login."
        )
        return redirect("accounts:user_list")

    return render(
        request,
        "accounts/set_password.html",
        {"form": form, "target_user": target_user},
    )

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_POST
def logout_beacon(request):
    """
    WHY: Called by navigator.sendBeacon when tab closes.
    sendBeacon cannot send CSRF tokens reliably so we
    exempt it — it only logs out the current session
    which requires being authenticated anyway.
    """
    from django.contrib.auth import logout as auth_logout
    from django.http import HttpResponse
    if request.user.is_authenticated:
        auth_logout(request)
    return HttpResponse(status=204)