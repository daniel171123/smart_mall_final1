from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import role_required
import os


@login_required
def home(request):
    if request.user.must_change_password:
        return redirect("accounts:change_password")
    if request.user.role == "SUPER_ADMIN":
        return _super_admin_dashboard(request)
    elif request.user.role == "MANAGER":
        return _manager_dashboard(request)
    elif request.user.role == "FINANCE":
        return _finance_dashboard(request)
    elif request.user.role == "TENANT":
        return _tenant_dashboard(request)
    return redirect("accounts:login")


def _get_user_mall(user):
    if user.role == "SUPER_ADMIN":
        return None
    try:
        return user.staff_profile.mall
    except Exception:
        return None


def _super_admin_dashboard(request):
    from malls.models import Mall, Shop
    from leases.models import Lease
    from invoices.models import Invoice
    from payments.models import Payment
    context = {
        "total_malls":      Mall.objects.count(),
        "total_shops":      Shop.objects.count(),
        "occupied_shops":   Shop.objects.filter(
                                status="OCCUPIED"
                            ).count(),
        "vacant_shops":     Shop.objects.filter(
                                status="VACANT"
                            ).count(),
        "active_leases":    Lease.objects.filter(
                                status="ACTIVE"
                            ).count(),
        "overdue_invoices": Invoice.objects.filter(
                                status="OVERDUE"
                            ).count(),
        "pending_payments": Payment.objects.filter(
                                status="PENDING_VERIFICATION"
                            ).count(),
        "recent_invoices":  Invoice.objects.select_related(
                                "lease__tenant__user",
                                "lease__shop"
                            ).order_by("-created_at")[:8],
        "recent_payments":  Payment.objects.select_related(
                                "tenant__user", "invoice"
                            ).order_by("-submitted_at")[:8],
    }
    return render(
        request, "dashboard/super_admin.html", context
    )


def _manager_dashboard(request):
    from leases.models import Lease
    from invoices.models import Invoice
    from payments.models import Payment
    from complaints.models import Complaint
    from tenants.models import TenantProfile
    from datetime import timedelta

    mall = _get_user_mall(request.user)
    lease_qs = Lease.objects.filter(status="ACTIVE")
    if mall:
        lease_qs = lease_qs.filter(shop__mall=mall)
    inv_qs = Invoice.objects.all()
    if mall:
        inv_qs = inv_qs.filter(lease__shop__mall=mall)
    pay_qs = Payment.objects.all()
    if mall:
        pay_qs = pay_qs.filter(
            invoice__lease__shop__mall=mall
        )
    context = {
        "total_tenants": (
            TenantProfile.objects.filter(
                leases__shop__mall=mall,
                leases__status="ACTIVE"
            ).distinct().count() if mall
            else TenantProfile.objects.count()
        ),
        "active_leases": lease_qs.count(),
        "expiring_leases": lease_qs.filter(
            end_date__lte=(
                timezone.now().date()
                + timedelta(days=30)
            )
        ).count(),
        "overdue_invoices": inv_qs.filter(
            status="OVERDUE"
        ).count(),
        "open_complaints": Complaint.objects.filter(
            status="OPEN"
        ).count(),
        "pending_payments": pay_qs.filter(
            status="PENDING_VERIFICATION"
        ).count(),
        "recent_leases": lease_qs.select_related(
            "tenant__user", "shop__mall"
        ).order_by("-created_at")[:6],
        "overdue_list": inv_qs.filter(
            status="OVERDUE"
        ).select_related(
            "lease__tenant__user"
        ).order_by("-due_date")[:6],
        "assigned_mall": mall,
    }
    return render(
        request, "dashboard/manager.html", context
    )


def _finance_dashboard(request):
    from invoices.models import Invoice
    from payments.models import Payment
    from django.db.models import Sum

    mall   = _get_user_mall(request.user)
    inv_qs = Invoice.objects.all()
    pay_qs = Payment.objects.all()
    if mall:
        inv_qs = inv_qs.filter(lease__shop__mall=mall)
        pay_qs = pay_qs.filter(
            invoice__lease__shop__mall=mall
        )
    total_collected = pay_qs.filter(
        status="VERIFIED"
    ).aggregate(t=Sum("amount_paid"))["t"] or 0
    context = {
        "pending_payments": pay_qs.filter(
            status="PENDING_VERIFICATION"
        ).count(),
        "verified_today": pay_qs.filter(
            status="VERIFIED",
            verified_at__date=timezone.now().date()
        ).count(),
        "overdue_invoices": inv_qs.filter(
            status="OVERDUE"
        ).count(),
        "total_collected": total_collected,
        "pending_list": pay_qs.filter(
            status="PENDING_VERIFICATION"
        ).select_related(
            "tenant__user", "invoice"
        ).order_by("-submitted_at")[:10],
        "assigned_mall": mall,
    }
    return render(
        request, "dashboard/finance.html", context
    )


def _tenant_dashboard(request):
    from invoices.models import Invoice
    from payments.models import Payment
    from complaints.models import Complaint
    try:
        tenant   = request.user.tenant_profile
        lease    = tenant.get_active_lease()
        invoices = Invoice.objects.filter(
            lease=lease
        ).order_by("-issue_date")[:5] if lease else []
        unpaid   = Invoice.objects.filter(
            lease=lease,
            status__in=["UNPAID", "OVERDUE"]
        ) if lease else Invoice.objects.none()
        context = {
            "tenant":          tenant,
            "lease":           lease,
            "recent_invoices": invoices,
            "unpaid_count":    unpaid.count(),
            "total_due":       sum(
                i.total_amount for i in unpaid
            ),
            "recent_payments": Payment.objects.filter(
                tenant=tenant
            ).order_by("-submitted_at")[:5],
            "open_complaints": Complaint.objects.filter(
                tenant=tenant, status="OPEN"
            ).count(),
        }
    except Exception:
        context = {
            "tenant": None, "lease": None,
            "recent_invoices": [], "unpaid_count": 0,
            "total_due": 0, "recent_payments": [],
            "open_complaints": 0,
        }
    return render(
        request, "dashboard/tenant.html", context
    )


@login_required
def reports(request):
    if request.user.role == "TENANT":
        messages.error(request, "Access denied.")
        return redirect("dashboard:home")
    return render(
        request,
        "dashboard/reports.html",
        _build_report_context(request)
    )


def _build_report_context(request):
    from invoices.models import Invoice
    from payments.models import Payment
    from leases.models import Lease
    from malls.models import Shop
    from django.db.models import Sum
    from django.db.models.functions import ExtractMonth
    import calendar

    mall  = _get_user_mall(request.user)
    today = timezone.now().date()

    inv_qs   = Invoice.objects.all()
    pay_qs   = Payment.objects.all()
    lease_qs = Lease.objects.all()
    if mall:
        inv_qs   = inv_qs.filter(lease__shop__mall=mall)
        pay_qs   = pay_qs.filter(
            invoice__lease__shop__mall=mall
        )
        lease_qs = lease_qs.filter(shop__mall=mall)

    total_collected  = pay_qs.filter(
        status="VERIFIED"
    ).aggregate(t=Sum("amount_paid"))["t"] or 0
    total_outstanding = inv_qs.filter(
        status__in=["UNPAID","OVERDUE"]
    ).aggregate(t=Sum("total_amount"))["t"] or 0
    total_penalty = inv_qs.aggregate(
        t=Sum("penalty_amount")
    )["t"] or 0

    inv_by_status = {
        "paid":    inv_qs.filter(status="PAID").count(),
        "unpaid":  inv_qs.filter(status="UNPAID").count(),
        "overdue": inv_qs.filter(status="OVERDUE").count(),
    }

    shop_qs        = Shop.objects.all()
    if mall:
        shop_qs = shop_qs.filter(mall=mall)
    total_shops    = shop_qs.count()
    occupied_shops = shop_qs.filter(
        status="OCCUPIED"
    ).count()
    vacant_shops   = shop_qs.filter(
        status="VACANT"
    ).count()
    occupancy_rate = (
        round(occupied_shops / total_shops * 100, 1)
        if total_shops > 0 else 0
    )

    monthly_raw = pay_qs.filter(
        status="VERIFIED",
        verified_at__year=today.year
    ).annotate(
        month_num=ExtractMonth("verified_at")
    ).values("month_num").annotate(
        total=Sum("amount_paid")
    ).order_by("month_num")

    monthly_collection = [
        {
            "month_name": calendar.month_name[
                row["month_num"]
            ],
            "total":     row["total"],
            "month_num": row["month_num"],
        }
        for row in monthly_raw
    ]

    from datetime import timedelta
    expiring = lease_qs.filter(
        status="ACTIVE",
        end_date__lte=today + timedelta(days=60),
        end_date__gte=today,
    ).select_related(
        "tenant__user", "shop__mall"
    ).order_by("end_date")

    backup_dir   = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "backups"
    )
    backup_files = []
    if os.path.exists(backup_dir):
        for f in sorted(
            os.listdir(backup_dir), reverse=True
        ):
            if f.endswith(".sql"):
                fp      = os.path.join(backup_dir, f)
                size_kb = os.path.getsize(fp) // 1024
                backup_files.append({
                    "name":    f,
                    "size_kb": size_kb,
                })

    return {
        "total_collected":    total_collected,
        "total_outstanding":  total_outstanding,
        "total_penalty":      total_penalty,
        "inv_by_status":      inv_by_status,
        "total_shops":        total_shops,
        "occupied_shops":     occupied_shops,
        "vacant_shops":       vacant_shops,
        "occupancy_rate":     occupancy_rate,
        "overdue_tenants":    inv_qs.filter(
            status="OVERDUE"
        ).select_related(
            "lease__tenant__user",
            "lease__shop__mall"
        ).order_by("-total_amount")[:10],
        "monthly_collection": monthly_collection,
        "expiring_leases":    expiring,
        "assigned_mall":      mall,
        "report_year":        today.year,
        "role":               request.user.role,
        "backup_files":       backup_files,
    }


@role_required("SUPER_ADMIN")
def run_backup(request):
    try:
        from django.core.management import call_command
        call_command("backup_db")
        messages.success(
            request,
            "Database backup created successfully."
        )
    except Exception as e:
        messages.error(request, f"Backup failed: {e}")
    return redirect("dashboard:reports")


@role_required("SUPER_ADMIN")
def restore_backup(request):
    if request.method != "POST":
        return redirect("dashboard:reports")

    backup_file = request.POST.get(
        "backup_file", ""
    ).strip()
    password    = request.POST.get("admin_password", "")

    if not request.user.check_password(password):
        messages.error(
            request,
            "Incorrect password. Restore cancelled."
        )
        return redirect("dashboard:reports")

    if not backup_file:
        messages.error(request, "No backup file selected.")
        return redirect("dashboard:reports")

    backup_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "backups"
    )
    full_path = os.path.join(backup_dir, backup_file)
    if not os.path.exists(full_path):
        messages.error(
            request,
            f"Backup file not found: {backup_file}"
        )
        return redirect("dashboard:reports")

    try:
        from django.core.management import call_command
        call_command("restore_db", file=full_path,
                     confirm=True)
        messages.success(
            request,
            f"Database restored from {backup_file}. "
            "Please restart the server."
        )
        try:
            from accounts.audit import audit_log
            audit_log(
                user=request.user,
                action="DATABASE_RESTORED",
                details=f"Restored from: {backup_file}",
                request=request,
            )
        except Exception:
            pass
    except Exception as e:
        messages.error(request, f"Restore failed: {e}")
    return redirect("dashboard:reports")


@role_required("SUPER_ADMIN")
def erase_data_view(request):
    """
    Erases EVERYTHING except the currently logged-in
    Super Admin account. Includes malls, shops, all
    other users, all financial data.
    Auto-creates backup before erasing.
    """
    if request.method != "POST":
        return redirect("dashboard:reports")

    password = request.POST.get("admin_password", "")
    confirm  = request.POST.get("confirm_text", "").strip()

    if not request.user.check_password(password):
        messages.error(
            request,
            "Incorrect password. Erase cancelled."
        )
        return redirect("dashboard:reports")

    if confirm != "ERASE":
        messages.error(
            request,
            'Type exactly "ERASE" to confirm.'
        )
        return redirect("dashboard:reports")

    # Step 1: Auto backup
    try:
        from django.core.management import call_command
        call_command("backup_db")
    except Exception as e:
        messages.error(
            request,
            f"Auto-backup failed ({e}). Erase aborted."
        )
        return redirect("dashboard:reports")

    # Step 2: Erase everything except current super admin
    try:
        from django.contrib.auth import get_user_model
        from accounts.models import AuditLog
        from notifications.models import Notification
        from complaints.models import Complaint
        from maintenance.models import MaintenanceRequest
        from payments.models import Payment
        from invoices.models import Invoice, PenaltyLog
        from leases.models import Lease
        from tenants.models import TenantProfile, StaffProfile
        from malls.models import Mall, Shop

        User = get_user_model()

        # Financial data first (FK order matters)
        PenaltyLog.objects.all().delete()
        Notification.objects.all().delete()
        AuditLog.objects.all().delete()
        Complaint.objects.all().delete()
        MaintenanceRequest.objects.all().delete()
        Payment.objects.all().delete()
        Invoice.objects.all().delete()
        Lease.objects.all().delete()

        # Profiles
        TenantProfile.objects.all().delete()
        StaffProfile.objects.all().delete()

        # All users except current super admin
        User.objects.exclude(
            pk=request.user.pk
        ).delete()

        # Physical structure
        Shop.objects.all().delete()
        Mall.objects.all().delete()

        # Audit the erase
        try:
            from accounts.audit import audit_log
            audit_log(
                user=request.user,
                action="FULL_SYSTEM_ERASE",
                details=(
                    "Full system erase performed. "
                    "Only Super Admin account preserved. "
                    "Auto-backup created before erase."
                ),
                request=request,
            )
        except Exception:
            pass

        messages.success(
            request,
            "Complete system reset done. "
            "All data erased (malls, shops, users, "
            "financial records). "
            "Your Super Admin account is preserved. "
            "An automatic backup was created first."
        )

    except Exception as e:
        messages.error(request, f"Erase failed: {e}")

    return redirect("dashboard:reports")
