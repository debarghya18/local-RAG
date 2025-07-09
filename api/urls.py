from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet)
router.register(r'rag-sessions', views.RAGSessionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('api.auth_urls')),
    path('upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('query/', views.RAGQueryView.as_view(), name='rag-query'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]