import psutil
import time
from django.utils import timezone
from django.http import JsonResponse
from django.core.cache import cache
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from documents.models import Document
from rag.models import RAGSession
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        checks = {
            'database': self._check_database(),
            'cache': self._check_cache(),
            'disk_space': self._check_disk_space(),
            'memory': self._check_memory(),
        }
        
        all_healthy = all(checks.values())
        
        return Response({
            'status': 'healthy' if all_healthy else 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'checks': checks
        }, status=200 if all_healthy else 503)
    
    def _check_database(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                return True
        except:
            return False
    
    def _check_cache(self):
        try:
            cache.set('health_check', 'ok', 1)
            return cache.get('health_check') == 'ok'
        except:
            return False
    
    def _check_disk_space(self):
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            return free_percent > 10  # More than 10% free
        except:
            return False
    
    def _check_memory(self):
        try:
            memory = psutil.virtual_memory()
            return memory.percent < 90  # Less than 90% used
        except:
            return False

class MetricsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        metrics = generate_latest()
        return Response(metrics, content_type=CONTENT_TYPE_LATEST)

class StatusView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'service': 'IntelliDocs',
            'version': '1.0.0',
            'timestamp': timezone.now().isoformat(),
            'uptime': self._get_uptime(),
            'stats': {
                'total_documents': Document.objects.count(),
                'processing_documents': Document.objects.filter(processing_status='processing').count(),
                'failed_documents': Document.objects.filter(processing_status='failed').count(),
                'total_sessions': RAGSession.objects.count(),
            }
        })
    
    def _get_uptime(self):
        # Simple uptime calculation (in production, use a more robust method)
        return time.time()