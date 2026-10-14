from django.urls import path
from . import views

app_name = 'malls'

urlpatterns = [
    path('',
         views.mall_list,    name='mall_list'),
    path('create/',
         views.mall_create,  name='mall_create'),
    path('<int:pk>/edit/',
         views.mall_edit,    name='mall_edit'),
    path('<int:pk>/delete/',
         views.mall_delete,  name='mall_delete'),
    path('shops/',
         views.shop_list,    name='shop_list'),
    path('shops/create/',
         views.shop_create,  name='shop_create'),
    path('shops/<int:pk>/edit/',
         views.shop_edit,    name='shop_edit'),
    path('shops/<int:pk>/delete/',
         views.shop_delete,  name='shop_delete'),
]