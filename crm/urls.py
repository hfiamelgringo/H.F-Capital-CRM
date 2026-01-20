from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.home, name='home'),
    path('import/', views.import_csv, name='import_csv'),
    path('ai-enrichment/', views.ai_enrichment, name='ai_enrichment'),
    path('enrichment-progress/', views.enrichment_progress, name='enrichment_progress'),
]
