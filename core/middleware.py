import time
import logging
from django.http import JsonResponse
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from typing import Callable, Any

logger = logging.getLogger(__name__)

class RateLimitMiddleware(MiddlewareMixin):
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Check rate limit
        cache_key = f"rate_limit:{ip}"
        requests = cache.get(cache_key, 0)
        
        if requests >= 100:  # 100 requests per hour
            return JsonResponse(
                {'error': 'Rate limit exceeded'}, 
                status=429
            )
        
        cache.set(cache_key, requests + 1, 3600)  # 1 hour
        return None

class LoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        request.start_time = time.time()
        logger.info(f"Request started: {request.method} {request.path}")
    
    def process_response(self, request, response):
        duration = time.time() - getattr(request, 'start_time', time.time())
        logger.info(
            f"Request completed: {request.method} {request.path} "
            f"Status: {response.status_code} Duration: {duration:.2f}s"
        )
        return response