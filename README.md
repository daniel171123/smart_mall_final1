# Smart Mall Management System

A Django application for managing mall operations, tenants, leases, invoices, payments, maintenance, complaints, and notifications.

## Features

- Role-aware accounts and dashboard
- Mall, tenant, and lease management
- Invoice and payment workflows
- Maintenance requests and complaints
- Notifications and scheduled reminders

## Requirements

- Python 3.12 or newer
- MySQL Server
- Redis for background jobs and scheduled tasks

## Local setup (Windows PowerShell)

1. Create and activate a virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install the Python dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

   Edit `.env` with your MySQL database name, username, and password. Generate a private Django key with:

   ```powershell
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   Put the generated value in `SECRET_KEY`. Keep `.env` private and never commit it.

4. Create the MySQL database, then apply migrations and start Django:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

5. Open <http://127.0.0.1:8000/>. Create an administrator account with `python manage.py createsuperuser` if needed.

For background tasks, start Redis and run a Celery worker and beat scheduler in separate terminals:

```powershell
celery -A core worker --loglevel=info
celery -A core beat --loglevel=info
```

## Configuration

See `.env.example` for required environment variable names. `DEBUG=True` uses Django's console email backend for local development. Before deployment, set `DEBUG=False`, configure `ALLOWED_HOSTS`, production email settings, and secure database credentials.

## Screenshots

No application screenshots are included yet. Add genuine screenshots of the running application here when available; do not include tenant documents, payment proofs, or other private data.

## Security

Do not commit `.env`, database backups, uploaded media, or real credentials. If a secret has ever been committed or shared, rotate it even after removing it from the latest version.
