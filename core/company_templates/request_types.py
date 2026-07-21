"""
Request Types Templates - أنواع الطلبات الافتراضية
يتم إضافتها تلقائياً لأي شركة جديدة عند إنشائها
كل نوع مربوط بفئة (Category) عن طريق category_key
"""

DEFAULT_REQUEST_TYPES = [
    # ═══════════════════════════════════════
    # 📋 طلبات إدارية
    # ═══════════════════════════════════════
    {
        'name': 'طلب شهادة عمل',
        'name_en': 'Employment Certificate',
        'category_key': 'طلبات إدارية',
        'description': 'طلب شهادة تثبت العمل في الشركة',
        'description_en': 'Request an employment certificate',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': '',
        'order': 1,
        'is_active': True,
    },
    {
        'name': 'طلب شهادة راتب',
        'name_en': 'Salary Certificate',
        'category_key': 'طلبات إدارية',
        'description': 'طلب شهادة تحدد الراتب',
        'description_en': 'Request a salary certificate',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': '',
        'order': 2,
        'is_active': True,
    },
    {
        'name': 'طلب تعديل بيانات',
        'name_en': 'Data Update Request',
        'category_key': 'طلبات إدارية',
        'description': 'طلب تعديل بيانات شخصية أو وظيفية',
        'description_en': 'Request to update personal or job data',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': True,
        'requires_approval': True,
        'permission_kind': '',
        'order': 3,
        'is_active': True,
    },

    # ═══════════════════════════════════════
    # 💰 طلبات مالية
    # ═══════════════════════════════════════
    {
        'name': 'طلب سلفة',
        'name_en': 'Advance Salary Request',
        'category_key': 'طلبات مالية',
        'description': 'طلب سلفة من الراتب',
        'description_en': 'Request salary advance',
        'requires_date_range': False,
        'requires_amount': True,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': '',
        'order': 1,
        'is_active': True,
    },
    {
        'name': 'طلب بدل مصروفات',
        'name_en': 'Expense Allowance',
        'category_key': 'طلبات مالية',
        'description': 'طلب استرداد مصروفات العمل',
        'description_en': 'Request work expenses reimbursement',
        'requires_date_range': False,
        'requires_amount': True,
        'requires_document': True,
        'requires_approval': True,
        'permission_kind': '',
        'order': 2,
        'is_active': True,
    },
    {
        'name': 'طلب مكافأة',
        'name_en': 'Bonus Request',
        'category_key': 'طلبات مالية',
        'description': 'طلب صرف مكافأة',
        'description_en': 'Request bonus payment',
        'requires_date_range': False,
        'requires_amount': True,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': '',
        'order': 3,
        'is_active': True,
    },

    # ═══════════════════════════════════════
    # ⏰ أذونات الحضور
    # ═══════════════════════════════════════
    {
        'name': 'إذن تأخير',
        'name_en': 'Late Permission',
        'category_key': 'أذونات الحضور',
        'description': 'إذن تأخير عن العمل',
        'description_en': 'Late arrival permission',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'late',
        'order': 1,
        'is_active': True,
    },
    {
        'name': 'إذن انصراف مبكر',
        'name_en': 'Early Leave Permission',
        'category_key': 'أذونات الحضور',
        'description': 'إذن انصراف قبل نهاية الدوام',
        'description_en': 'Early leave permission',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'early_leave',
        'order': 2,
        'is_active': True,
    },
    {
        'name': 'إذن خروج مؤقت',
        'name_en': 'Temporary Exit Permission',
        'category_key': 'أذونات الحضور',
        'description': 'إذن خروج مؤقت أثناء الدوام',
        'description_en': 'Temporary exit permission during work',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'exit',
        'order': 3,
        'is_active': True,
    },

    # ═══════════════════════════════════════
    # 📌 أخرى
    # ═══════════════════════════════════════
    {
        'name': 'طلب آخر',
        'name_en': 'Other Request',
        'category_key': 'أخرى',
        'description': 'أي طلب آخر غير مذكور',
        'description_en': 'Any other request',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': '',
        'order': 1,
        'is_active': True,
    },
]
