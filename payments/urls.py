from django.urls import path
from . import views
from .receipt import download_receipt

app_name = 'payments'

urlpatterns = [
    path('',
         views.payment_list,
         name='payment_list'),
    path('my/',
         views.my_payments,
         name='my_payments'),
    path('submit/<int:inv_pk>/',
         views.submit_payment,
         name='submit_payment'),
    path('verify/<int:pk>/',
         views.verify_payment,
         name='verify_payment'),
    path('receipt/<int:payment_pk>/',
         download_receipt,
         name='download_receipt'),
]