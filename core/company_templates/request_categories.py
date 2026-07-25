"""
Request Categories Templates - فئات الطلبات الافتراضية
يتم إضافتها تلقائياً لأي شركة جديدة عند إنشائها
"""

DEFAULT_REQUEST_CATEGORIES = [
    {
        'name': 'الحضور والانصراف',
        'name_en': 'Attendance',
        'icon': 'bi-clock-history',
        'color': '#2563EB',
        'order': 1,
        'is_active': True,
    },
    {
        'name': 'مالية',
        'name_en': 'Financial',
        'icon': 'bi-cash-coin',
        'color': '#16A34A',
        'order': 2,
        'is_active': True,
    },
    {
        'name': 'موارد بشرية',
        'name_en': 'HR Services',
        'icon': 'bi-person-badge',
        'color': '#7C3AED',
        'order': 3,
        'is_active': True,
    },
    {
        'name': 'إدارية وتشغيلية',
        'name_en': 'Administrative',
        'icon': 'bi-gear',
        'color': '#D97706',
        'order': 4,
        'is_active': True,
    },
    {
        'name': 'عام',
        'name_en': 'General',
        'icon': 'bi-chat-square-text',
        'color': '#64748B',
        'order': 5,
        'is_active': True,
    },
]
