"""
Job Titles Templates - المسميات الوظيفية الافتراضية
يتم إضافتها تلقائياً لأي شركة جديدة عند إنشائها
العميل يقدر يعدل عليها أو يمسحها أو يضيف جديد
"""

DEFAULT_JOB_TITLES = [
    # === الإدارة العليا ===
    {'name_ar': 'مدير عام', 'name_en': 'General Manager'},
    {'name_ar': 'مدير', 'name_en': 'Manager'},

    # === الموارد البشرية ===
    {'name_ar': 'مدير موارد بشرية', 'name_en': 'HR Manager'},
    {'name_ar': 'موظف موارد بشرية', 'name_en': 'HR Officer'},

    # === المالية ===
    {'name_ar': 'مدير مالي', 'name_en': 'Finance Manager'},
    {'name_ar': 'محاسب', 'name_en': 'Accountant'},
    {'name_ar': 'مسؤول رواتب', 'name_en': 'Payroll Officer'},

    # === العمليات ===
    {'name_ar': 'مدير عمليات', 'name_en': 'Operations Manager'},
    {'name_ar': 'مشرف', 'name_en': 'Supervisor'},

    # === المبيعات وخدمة العملاء ===
    {'name_ar': 'مندوب مبيعات', 'name_en': 'Sales Executive'},
    {'name_ar': 'خدمة عملاء', 'name_en': 'Customer Service'},

    # === الميدان والمخازن ===
    {'name_ar': 'موظف ميداني', 'name_en': 'Field Officer'},
    {'name_ar': 'أمين مخزن', 'name_en': 'Warehouse Keeper'},

    # === الدعم الفني ===
    {'name_ar': 'دعم فني', 'name_en': 'IT Support'},

    # === موظف عام ===
    {'name_ar': 'موظف', 'name_en': 'Employee'},
]
