"""
Leave Types Templates - أنواع الإجازات الافتراضية
يتم إضافتها تلقائياً لأي شركة جديدة عند إنشائها
العميل يقدر يعدل الأيام، الخصائص، أو يضيف/يمسح أنواع
"""

DEFAULT_LEAVE_TYPES = [
    {
        'name': 'إجازة سنوية',
        'name_en': 'Annual Leave',
        'category': 'annual',
        'days_allowed': 21,
        'is_paid': True,
        'requires_approval': True,
        'requires_document': False,
        'carry_forward': True,
        'max_carry_days': 5,
        'color': '#4CAF50',  # أخضر
        'description': 'الإجازة السنوية المستحقة للموظف',
        'is_active': True,
    },
    {
        'name': 'إجازة مرضية',
        'name_en': 'Sick Leave',
        'category': 'sick',
        'days_allowed': 14,
        'is_paid': True,
        'requires_approval': True,
        'requires_document': True,  # تحتاج تقرير طبي
        'carry_forward': False,
        'max_carry_days': 0,
        'color': '#F44336',  # أحمر
        'description': 'إجازة مرضية بتقرير طبي',
        'is_active': True,
    },
    {
        'name': 'إجازة طارئة',
        'name_en': 'Emergency Leave',
        'category': 'emergency',
        'days_allowed': 7,
        'is_paid': True,
        'requires_approval': True,
        'requires_document': False,
        'carry_forward': False,
        'max_carry_days': 0,
        'color': '#FF9800',  # برتقالي
        'description': 'إجازة طارئة لظروف قاهرة',
        'is_active': True,
    },
    {
        'name': 'إجازة بدون مرتب',
        'name_en': 'Unpaid Leave',
        'category': 'unpaid',
        'days_allowed': 30,
        'is_paid': False,
        'requires_approval': True,
        'requires_document': False,
        'carry_forward': False,
        'max_carry_days': 0,
        'color': '#9E9E9E',  # رمادي
        'description': 'إجازة بدون أجر',
        'is_active': True,
    },
    {
        'name': 'إجازة أمومة',
        'name_en': 'Maternity Leave',
        'category': 'other',
        'days_allowed': 90,
        'is_paid': True,
        'requires_approval': True,
        'requires_document': True,  # تحتاج شهادة طبية
        'carry_forward': False,
        'max_carry_days': 0,
        'color': '#E91E63',  # وردي
        'description': 'إجازة الوضع للموظفات',
        'is_active': True,
    },
]
