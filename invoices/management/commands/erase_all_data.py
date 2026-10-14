
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = (
        "Erase all operational data. "
        "Creates an automatic backup first. "
        "Requires admin password confirmation."
    )

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(
            self.style.WARNING(
                "\n" + "=" * 55 + "\n"
                "  ERASE ALL DATA\n"
                "=" * 55 + "\n"
                "This will permanently delete:\n"
                "  - All invoices and penalty logs\n"
                "  - All payments\n"
                "  - All leases\n"
                "  - All tenants and their profiles\n"
                "  - All complaints\n"
                "  - All maintenance requests\n"
                "  - All notifications\n"
                "  - All audit logs\n"
                "\nStaff accounts (Admin/Manager/Finance)\n"
                "and Malls/Shops will be preserved.\n"
                + "=" * 55
            )
        )

        # Step 1: Require admin password
        import getpass
        email    = input("\nEnter your Super Admin email: ").strip()
        password = getpass.getpass("Enter your password: ")

        try:
            user = User.objects.get(
                email=email, role="SUPER_ADMIN"
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "No Super Admin found with that email."
                )
            )
            return

        if not user.check_password(password):
            self.stdout.write(
                self.style.ERROR("Incorrect password. Aborted.")
            )
            return

        # Step 2: Final confirmation
        confirm = input(
            "\nType ERASE to confirm permanent deletion: "
        ).strip()
        if confirm != "ERASE":
            self.stdout.write("Aborted. Nothing was deleted.")
            return

        # Step 3: Auto backup before erasing
        self.stdout.write(
            "\nCreating automatic backup before erasing..."
        )
        try:
            from django.core.management import call_command
            call_command("backup_db")
            self.stdout.write(
                self.style.SUCCESS("Backup created successfully.")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Backup failed: {e}")
            )
            abort = input(
                "Backup failed. Continue anyway? (yes/no): "
            )
            if abort.lower() != "yes":
                self.stdout.write("Aborted.")
                return

        # Step 4: Delete all operational data
        self.stdout.write("\nErasing data...")

        from accounts.models import AuditLog
        from notifications.models import Notification
        from complaints.models import Complaint
        from maintenance.models import MaintenanceRequest
        from payments.models import Payment
        from invoices.models import Invoice, PenaltyLog
        from leases.models import Lease
        from tenants.models import TenantProfile

        counts = {}
        counts["PenaltyLog"]         = PenaltyLog.objects.count()
        counts["Notification"]       = Notification.objects.count()
        counts["AuditLog"]           = AuditLog.objects.count()
        counts["Complaint"]          = Complaint.objects.count()
        counts["MaintenanceRequest"] = (
            MaintenanceRequest.objects.count()
        )
        counts["Payment"]    = Payment.objects.count()
        counts["Invoice"]    = Invoice.objects.count()
        counts["Lease"]      = Lease.objects.count()
        counts["Tenant"]     = TenantProfile.objects.count()

        PenaltyLog.objects.all().delete()
        Notification.objects.all().delete()
        AuditLog.objects.all().delete()
        Complaint.objects.all().delete()
        MaintenanceRequest.objects.all().delete()
        Payment.objects.all().delete()
        Invoice.objects.all().delete()
        Lease.objects.all().delete()

        # Delete tenant user accounts
        tenant_users = User.objects.filter(role="TENANT")
        tenant_count = tenant_users.count()
        tenant_users.delete()

        # Reset shop statuses to VACANT
        from malls.models import Shop
        Shop.objects.all().update(status="VACANT")

        self.stdout.write(
            self.style.SUCCESS(
                "\n" + "=" * 55 + "\n"
                "  ERASE COMPLETE\n"
                "=" * 55
            )
        )
        for model, count in counts.items():
            self.stdout.write(f"  Deleted {count:>5} {model}")
        self.stdout.write(
            f"  Deleted {tenant_count:>5} Tenant user accounts"
        )
        self.stdout.write(
            "  Reset all shops to VACANT"
        )
        self.stdout.write(
            "\nStaff accounts and mall/shop structure preserved."
            "\nRestart the server to reflect changes.\n"
        )

        # Audit the erase action itself
        try:
            from accounts.audit import audit_log
            audit_log(
                user=user,
                action="SYSTEM_DATA_ERASED",
                details=(
                    "All operational data erased by admin. "
                    "Auto-backup created first."
                ),
            )
        except Exception:
            pass
