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
        """
        اسم المستخدم الأول (فريد)، وبعدين الإيميل أو الموبايل، وبعدين الرقم الوظيفي.
        الإيميل/الموبايل/الرقم الوظيفي لازم يطابقوا حساب واحد بس — الرقم الوظيفي بيتكرر بين الشركات
        (EMP00001 في كل شركة)، فلو اتكرر مانخمنش (عشان محدش يدخل حساب شركة تانية).
        """
        username = (username or '').strip()
        if not username:
            return None
        user = User.objects.filter(username__iexact=username).first()
        if user:
            return user

        users = list(User.objects.filter(Q(email__iexact=username) | Q(phone=username))[:2])
        if len(users) == 1:
            return users[0]
        if users:
            return None

        from employees.models import Employee
        # _base_manager: وقت الدخول مفيش شركة محددة، فـ objects كانت بترجع فاضي
        emps = list(Employee._base_manager.filter(
            employee_code__iexact=username, user__isnull=False,
        ).select_related('user')[:2])
        if len(emps) == 1:
            return emps[0].user
        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
