"""
JWT: نفس قواعد الدخول — الحساب الموقوف أو الشركة الموقوفة مايطلعلهمش توكن جديد.
"""
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from .access import block_reason, blocked_payload


def _deny(user):
    reason = block_reason(user)
    if reason:
        raise exceptions.PermissionDenied(blocked_payload(reason))


class AccessTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        _deny(self.user)
        return data


class AccessTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            user_id = RefreshToken(attrs['refresh'])[api_settings.USER_ID_CLAIM]
        except Exception:
            user_id = None
        if user_id is not None:
            user = get_user_model()._base_manager.filter(**{api_settings.USER_ID_FIELD: user_id}).first()
            if user:
                _deny(user)
        return super().validate(attrs)
