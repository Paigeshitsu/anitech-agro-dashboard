from django.urls import path
from . import views

app_name = 'crops'

urlpatterns = [
    path('', views.crops_list, name='crops'),
    path('available/', views.available_crops, name='available_crops'),
    path('add/', views.crop_add, name='crop_add'),
    path('<int:crop_id>/', views.crop_view, name='crop_detail'),
    path('<int:crop_id>/edit/', views.crop_edit, name='crop_edit'),
    path('<int:crop_id>/delete/', views.crop_delete, name='crop_delete'),
    path('<int:crop_id>/purchase/', views.crop_purchase, name='crop_purchase'),
]

