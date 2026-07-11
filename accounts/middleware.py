"""
middleware.py - accounts
إجبار تغيير كلمة المرور عند أول دخول
"""

from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """
    لو المستخدم must_change_password = True
    يتحول أوتوماتيك لصفحة تغيير كلمة المرور
    """

    # الصفحات المسموح بها بدون تغيير
    EXEMPT_URLS = [
        '/password-change/',
        '/password-change/done/',
        '/logout/',
        '/login/',
        '/admin/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and hasattr(request.user, 'must_change_password')
            and request.user.must_change_password
            and not request.user.is_superuser
        ):
            # تحقق إن المسار مش معفي
            path = request.path_info
            exempt = any(path.startswith(url) for url in self.EXEMPT_URLS)

            if not exempt:
                return redirect('/password-change/')

        return self.get_response(request)
