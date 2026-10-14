from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import subprocess
import os


class Command(BaseCommand):
    help = (
        'Create a full MySQL database backup. '
        'Saves to backups/ folder with timestamp.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directory to save backup files'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        db       = settings.DATABASES['default']
        db_name  = db['NAME']
        db_user  = db['USER']
        db_pass  = db['PASSWORD']
        db_host  = db.get('HOST', 'localhost')
        db_port  = db.get('PORT', '3306')

        timestamp = timezone.now().strftime(
            '%Y%m%d_%H%M%S'
        )
        filename  = os.path.join(
            output_dir,
            f'smartmall_backup_{timestamp}.sql'
        )

        self.stdout.write(
            f'Creating backup: {filename}...'
        )

        # Build mysqldump command
        cmd = [
            'mysqldump',
            f'--host={db_host}',
            f'--port={db_port}',
            f'--user={db_user}',
            f'--password={db_pass}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--add-drop-table',
            db_name,
        ]

        try:
            with open(filename, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )

            if result.returncode == 0:
                size = os.path.getsize(filename)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Backup created successfully!\n'
                        f'  File: {filename}\n'
                        f'  Size: {size:,} bytes\n'
                        f'  Time: {timestamp}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Backup failed:\n{result.stderr}'
                    )
                )
                os.remove(filename)

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    'mysqldump not found. Make sure MySQL '
                    'client tools are installed and in PATH.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup error: {e}')
            )