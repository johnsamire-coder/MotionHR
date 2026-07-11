"""
breadcrumb_processor.py
Context processor يولّد breadcrumbs تلقائي حسب الـ URL
"""


def breadcrumb_processor(request):
    """
    يولد breadcrumbs تلقائيًا من الـ URL
    ولو الـ view بعت breadcrumbs في الـ context يستخدمها بدلاً منه
    """
    path = request.path_info
    breadcrumbs = []

    # خريطة المسارات
    path_map = {
        "/employees/": "الموظفون",
        "/employees/add/": "إضافة موظف",
        "/attendance/": "الحضور",
        "/attendance/check-in/": "تسجيل الحضور",
        "/attendance/map/": "الخريطة الحية",
        "/attendance/monitor/": "متابعة الميدانيين",
        "/attendance/visits/": "الزيارات",
        "/attendance/schedule/": "جدول العمل",
        "/attendance/late-notifications/": "إشعارات التأخير",
        "/attendance/stealth-manage/": "إدارة التتبع",
        "/attendance/stealth-alerts/": "تنبيهات التتبع",
        "/attendance/my-warnings/": "إنذاراتي",
        "/leaves/": "الإجازات",
        "/leaves/add/": "طلب إجازة",
        "/leaves/types/": "أنواع الإجازات",
        "/leaves/balances/": "أرصدة الإجازات",
        "/requests/": "الطلبات",
        "/requests/add/": "طلب جديد",
        "/reports/": "التقارير",
        "/reports/attendance/": "تقرير الحضور",
        "/reports/late/": "تقرير التأخيرات",
        "/reports/leaves/": "تقرير الإجازات",
        "/reports/field/": "تقرير الميدانيين",
        "/reports/employees/": "تقرير الموظفين",
        "/companies/settings/": "إعدادات الشركة",
        "/companies/branches/": "الفروع",
        "/companies/branches/add/": "إضافة فرع",
        "/companies/departments/": "الإدارات",
        "/companies/departments/add/": "إضافة إدارة",
        "/companies/shifts/": "الشيفتات",
        "/companies/shifts/add/": "إضافة شيفت",
        "/companies/charter/": "ميثاق العمل",
        "/companies/charter/manage/": "إدارة الميثاق",
        "/companies/policies/": "السياسات والقواعد",
        "/companies/approval-flows/": "مسارات الموافقة",
        "/companies/delegations/": "التفويضات",
        "/companies/delegations/add/": "إضافة تفويض",
        "/subscriptions/my-plan/": "خطتي",
        "/subscriptions/contact-sales/": "تواصل / ترقية",
        "/accounts/profile/": "الملف الشخصي",
        "/accounts/notifications/": "الإشعارات",
        "/accounts/notifications/send/": "إرسال إشعار",
        "/accounts/login-settings/": "إعدادات الدخول",
        "/employees/my-balance/": "رصيد إجازاتي",
        "/employees/my-deductions/": "خصوماتي",
        "/search/": "البحث",
        "/password-change/": "تغيير كلمة المرور",
    }

    # نبني الـ breadcrumbs من المسار
    # نبص على الـ sections
    section_map = {
        "/employees/": {"label": "الموظفون", "url": "/employees/"},
        "/attendance/": {"label": "الحضور", "url": "/attendance/"},
        "/leaves/": {"label": "الإجازات", "url": "/leaves/"},
        "/requests/": {"label": "الطلبات", "url": "/requests/"},
        "/reports/": {"label": "التقارير", "url": "/reports/"},
        "/companies/": {"label": "الشركة", "url": "/companies/settings/"},
        "/subscriptions/": {"label": "الاشتراك", "url": "/subscriptions/my-plan/"},
        "/accounts/": {"label": "حسابي", "url": "/accounts/profile/"},
    }

    # لو الصفحة هي Dashboard ذاتها
    if path == "/dashboard/":
        return {"breadcrumbs": []}

    # نبحث عن القسم
    for section_path, section_info in section_map.items():
        if path.startswith(section_path):
            # لو القسم مش هو الصفحة نفسها
            if path != section_path:
                breadcrumbs.append({
                    "label": section_info["label"],
                    "url": section_info["url"]
                })

            # لو الصفحة معروفة
            page_label = path_map.get(path)
            if page_label and page_label != section_info["label"]:
                breadcrumbs.append({
                    "label": page_label,
                    "url": None
                })
            elif page_label:
                breadcrumbs.append({
                    "label": page_label,
                    "url": None
                })
            break

    # لو مفيش match
    if not breadcrumbs:
        label = path_map.get(path)
        if label:
            breadcrumbs.append({"label": label, "url": None})

    return {"breadcrumbs": breadcrumbs}


def vapid_key_processor(request):
    """يوفر VAPID_PUBLIC_KEY للـ templates"""
    from django.conf import settings
    return {
        "VAPID_PUBLIC_KEY": getattr(settings, "VAPID_PUBLIC_KEY", ""),
    }
