from django.apps import AppConfig


class LeasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leases'

    def ready(self):
        # WHY: Import signals here so they register
        # when Django starts up
        import leases.signals