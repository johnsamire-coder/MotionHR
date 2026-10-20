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

        try:
            user = self.find_user(username)
            # الحساب الموقوف مايدخلش (user_can_authenticate بيشيك على is_active)
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user

        except Exception:
            return None

        return None

    @staticmethod
    def find_user(username):
        """بنبحث بكل الطرق في وقت واحد، ولو مش لاقيه نجرب الرقم الوظيفي"""
        username = (username or '').strip()
        if not username:
            return None
        user = User.objects.filter(
            Q(username__iexact=username) |
            Q(email__iexact=username) |
            Q(phone=username)
        ).first()

        if not user:
            from employees.models import Employee
            emp = Employee.objects.filter(
                employee_code__iexact=username
            ).select_related('user').first()
            if emp and emp.user:
                user = emp.user
        return user

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
