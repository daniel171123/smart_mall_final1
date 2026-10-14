from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os


class Command(BaseCommand):
    help = (
        'Restore MySQL database from a backup file. '
        'Usage: python manage.py restore_db '
        '--file backups/smartmall_backup_TIMESTAMP.sql'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to the SQL backup file to restore'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        backup_file = options['file']

        if not os.path.exists(backup_file):
            self.stdout.write(
                self.style.ERROR(
                    f'Backup file not found: {backup_file}'
                )
            )
            return

        size = os.path.getsize(backup_file)
        self.stdout.write(
            f'\nBackup file: {backup_file}'
            f'\nFile size:   {size:,} bytes'
        )

        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  WARNING: This will OVERWRITE the '
                    'current database.\n'
                    'All current data will be replaced '
                    'with the backup data.\n'
                )
            )
            confirm = input(
                'Type "yes" to confirm restore: '
            )
            if confirm.lower() != 'yes':
                self.stdout.write('Restore cancelled.')
                return

        db      = settings.DATABASES['default']
        db_name = db['NAME']
        db_user = db['USER']
        db_pass = db['PASSWORD']
        db_host = db.get('HOST', 'localhost')
        db_port = db.get('PORT', '3306')

        self.stdout.write('\nRestoring database...')

        cmd = [
            'mysql',
            f'--host={db_host}',
            f'--port={db_port}',
            f'--user={db_user}',
            f'--password={db_pass}',
            db_name,
        ]

        try:
            with open(backup_file, 'r') as f:
                result = subprocess.run(
                    cmd,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    text=True
                )

            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        '\nDatabase restored successfully!\n'
                        f'  Source: {backup_file}\n'
                        f'  Database: {db_name}\n\n'
                        'Restart the Django server to '
                        'apply changes.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Restore failed:\n{result.stderr}'
                    )
                )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    'mysql client not found. Make sure '
                    'MySQL client tools are in PATH.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Restore error: {e}')
            )