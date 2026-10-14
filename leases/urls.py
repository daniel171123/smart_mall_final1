from django.urls import path
from . import views

app_name = 'leases'

urlpatterns = [
    path('',
         views.lease_list,      name='lease_list'),
    path('create/',
         views.lease_create,    name='lease_create'),
    path('<int:pk>/',
         views.lease_detail,    name='lease_detail'),
    path('<int:pk>/terminate/',
         views.lease_terminate, name='lease_terminate'),
]