
from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("",
         views.home,
         name="home"),
    path("reports/",
         views.reports,
         name="reports"),
    path("backup/",
         views.run_backup,
         name="run_backup"),
    path("restore/",
         views.restore_backup,
         name="restore_backup"),
    path("erase/",
         views.erase_data_view,
         name="erase_data"),
]
