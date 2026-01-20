from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('', views.company_list, name='company_list'),
    path('create/', views.company_create, name='company_create'),
    path('<str:pk>/edit/', views.company_update, name='company_update'),
    path('<str:pk>/delete/', views.company_delete, name='company_delete'),
    path('<str:pk>/view/', views.company_detail, name='company_detail'),
]
