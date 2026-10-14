from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('',
         views.complaint_list,
         name='complaint_list'),
    path('my/',
         views.my_complaints,
         name='my_complaints'),
    path('create/',
         views.complaint_create,
         name='complaint_create'),
    path('<int:pk>/',
         views.complaint_detail,
         name='complaint_detail'),
]