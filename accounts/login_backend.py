"""
login_backend.py
Backend تسجيل الدخول الذكي
يدعم: username / email / employee_code / phone
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class SmartLoginBackend(ModelBackend):
    """
    Backend ذكي يحاول تسجيل الدخول بـ:
    1. username (دايماً)
    2. email (لو مفعّل للشركة)
    3. employee_code (لو مفعّل للشركة)
    4. phone (لو مفعّل للشركة)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        username = username.strip()

        try:
            # نبحث بكل الطرق في وقت واحد
            user = User.objects.filter(
                Q(username__iexact=username) |
                Q(email__iexact=username) |
                Q(phone=username)
            ).first()

            # لو مش لاقيه جرب الرقم الوظيفي
            if not user:
                from employees.models import Employee
                emp = Employee.objects.filter(
                    employee_code__iexact=username
                ).select_related('user').first()
                if emp and emp.user:
                    user = emp.user

            if user and user.check_password(password):
                return user

        except Exception:
            return None

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
