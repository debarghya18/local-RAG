from django.urls import path
from . import views

urlpatterns = [
    path('', views.HealthCheckView.as_view(), name='health-check'),
    path('metrics/', views.MetricsView.as_view(), name='metrics'),
    path('status/', views.StatusView.as_view(), name='status'),
]