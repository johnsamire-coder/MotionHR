"""
Request Categories Templates - فئات الطلبات الافتراضية
يتم إضافتها تلقائياً لأي شركة جديدة عند إنشائها
"""

DEFAULT_REQUEST_CATEGORIES = [
    {
        'name': 'طلبات إدارية',
        'name_en': 'Administrative Requests',
        'icon': 'assignment',
        'color': '#1976D2',  # أزرق
        'order': 1,
        'is_active': True,
    },
    {
        'name': 'طلبات مالية',
        'name_en': 'Financial Requests',
        'icon': 'payments',
        'color': '#2E7D32',  # أخضر
        'order': 2,
        'is_active': True,
    },
    {
        'name': 'أذونات الحضور',
        'name_en': 'Attendance Permissions',
        'icon': 'access_time',
        'color': '#F57C00',  # برتقالي
        'order': 3,
        'is_active': True,
    },
    {
        'name': 'أخرى',
        'name_en': 'Other',
        'icon': 'more_horiz',
        'color': '#757575',  # رمادي
        'order': 99,
        'is_active': True,
    },
]
