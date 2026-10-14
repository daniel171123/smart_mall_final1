from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('',
         views.request_list,
         name='request_list'),
    path('my/',
         views.my_requests,
         name='my_requests'),
    path('create/',
         views.request_create,
         name='request_create'),
    path('<int:pk>/',
         views.request_detail,
         name='request_detail'),
]