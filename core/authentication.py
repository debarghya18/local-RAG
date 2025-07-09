import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from datetime import datetime, timedelta
from typing import Optional, Tuple, Any


User = get_user_model()

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request) -> Optional[tuple[Any, str]]:
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None
        
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        
        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
        
        return (user, token)

def generate_jwt_token(user) -> str:
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def decode_jwt_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])