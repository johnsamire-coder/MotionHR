"""
Request Types Templates - أنواع الطلبات الافتراضية
يتم إضافتها تلقائياً لأي شركة جديدة عند إنشائها
كل نوع مربوط بفئة (Category) عن طريق category_key
"""

DEFAULT_REQUEST_TYPES = [
    # ═══════════════════════════════════════
    # الحضور والانصراف
    # ═══════════════════════════════════════
    {
        'name': 'إذن تأخير',
        'name_en': 'Late Arrival Permission',
        'category_key': 'الحضور والانصراف',
        'description': 'طلب إذن للحضور متأخراً مع خصم من رصيد الأذونات',
        'description_en': 'Request permission to arrive late',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'late_arrival',
        'order': 1,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'permission_date', 'label_ar': 'تاريخ الإذن', 'label_en': 'Permission Date', 'type': 'date', 'required': True},
                {'key': 'permission_time', 'label_ar': 'وقت الحضور المتوقع', 'label_en': 'Expected Arrival Time', 'type': 'time', 'required': True},
                {'key': 'duration_hours', 'label_ar': 'مدة الإذن (ساعات)', 'label_en': 'Duration (hours)', 'type': 'number', 'required': True},
                {'key': 'reason', 'label_ar': 'السبب', 'label_en': 'Reason', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'إذن خروج مبكر',
        'name_en': 'Early Leave Permission',
        'category_key': 'الحضور والانصراف',
        'description': 'طلب إذن للانصراف قبل نهاية الشيفت',
        'description_en': 'Request permission to leave early',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'early_leave',
        'order': 2,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'permission_date', 'label_ar': 'تاريخ الإذن', 'label_en': 'Permission Date', 'type': 'date', 'required': True},
                {'key': 'permission_time', 'label_ar': 'وقت الانصراف المطلوب', 'label_en': 'Requested Leave Time', 'type': 'time', 'required': True},
                {'key': 'duration_hours', 'label_ar': 'مدة الإذن (ساعات)', 'label_en': 'Duration (hours)', 'type': 'number', 'required': True},
                {'key': 'reason', 'label_ar': 'السبب', 'label_en': 'Reason', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'تعديل سجل حضور',
        'name_en': 'Attendance Correction',
        'category_key': 'الحضور والانصراف',
        'description': 'طلب تصحيح وقت الحضور أو الانصراف',
        'description_en': 'Request to correct attendance record',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 3,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'attendance_date', 'label_ar': 'تاريخ اليوم', 'label_en': 'Date', 'type': 'date', 'required': True},
                {'key': 'correction_type', 'label_ar': 'نوع التعديل', 'label_en': 'Correction Type', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'check_in', 'label_ar': 'تعديل وقت الحضور', 'label_en': 'Fix Check-in'},
                     {'value': 'check_out', 'label_ar': 'تعديل وقت الانصراف', 'label_en': 'Fix Check-out'},
                     {'value': 'both', 'label_ar': 'تعديل الحضور والانصراف', 'label_en': 'Fix Both'},
                     {'value': 'full_day', 'label_ar': 'تصحيح يوم كامل', 'label_en': 'Full Day Correction'},
                 ]},
                {'key': 'correct_check_in', 'label_ar': 'وقت الحضور الصحيح', 'label_en': 'Correct Check-in Time', 'type': 'time', 'required': False},
                {'key': 'correct_check_out', 'label_ar': 'وقت الانصراف الصحيح', 'label_en': 'Correct Check-out Time', 'type': 'time', 'required': False},
                {'key': 'reason', 'label_ar': 'السبب', 'label_en': 'Reason', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'تبرير غياب',
        'name_en': 'Absence Justification',
        'category_key': 'الحضور والانصراف',
        'description': 'تقديم عذر عن يوم غياب',
        'description_en': 'Justify an absence day',
        'requires_date_range': True,
        'requires_amount': False,
        'requires_document': True,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 4,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'start_date', 'label_ar': 'من تاريخ', 'label_en': 'From Date', 'type': 'date', 'required': True},
                {'key': 'end_date', 'label_ar': 'إلى تاريخ', 'label_en': 'To Date', 'type': 'date', 'required': True},
                {'key': 'reason', 'label_ar': 'سبب الغياب', 'label_en': 'Absence Reason', 'type': 'textarea', 'required': True},
            ]
        }
    },

    # ═══════════════════════════════════════
    # مالية
    # ═══════════════════════════════════════
    {
        'name': 'سلفة',
        'name_en': 'Advance Salary',
        'category_key': 'مالية',
        'description': 'طلب سلفة من الراتب',
        'description_en': 'Request salary advance',
        'requires_date_range': False,
        'requires_amount': True,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 1,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'amount', 'label_ar': 'المبلغ المطلوب', 'label_en': 'Requested Amount', 'type': 'number', 'required': True},
                {'key': 'installments', 'label_ar': 'عدد أقساط السداد', 'label_en': 'Number of Installments', 'type': 'number', 'required': True},
                {'key': 'reason', 'label_ar': 'السبب', 'label_en': 'Reason', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'قرض',
        'name_en': 'Loan',
        'category_key': 'مالية',
        'description': 'طلب قرض من الشركة',
        'description_en': 'Request a company loan',
        'requires_date_range': False,
        'requires_amount': True,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 2,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'amount', 'label_ar': 'مبلغ القرض', 'label_en': 'Loan Amount', 'type': 'number', 'required': True},
                {'key': 'installments', 'label_ar': 'عدد أقساط السداد', 'label_en': 'Number of Installments', 'type': 'number', 'required': True},
                {'key': 'purpose', 'label_ar': 'الغرض من القرض', 'label_en': 'Loan Purpose', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'رد مصروفات',
        'name_en': 'Expense Reimbursement',
        'category_key': 'مالية',
        'description': 'طلب استرداد مصروفات العمل',
        'description_en': 'Request reimbursement for work expenses',
        'requires_date_range': True,
        'requires_amount': True,
        'requires_document': True,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 3,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'start_date', 'label_ar': 'من تاريخ', 'label_en': 'From Date', 'type': 'date', 'required': True},
                {'key': 'end_date', 'label_ar': 'إلى تاريخ', 'label_en': 'To Date', 'type': 'date', 'required': True},
                {'key': 'amount', 'label_ar': 'المبلغ الإجمالي', 'label_en': 'Total Amount', 'type': 'number', 'required': True},
                {'key': 'expense_type', 'label_ar': 'نوع المصروف', 'label_en': 'Expense Type', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'transport', 'label_ar': 'مواصلات', 'label_en': 'Transportation'},
                     {'value': 'meals', 'label_ar': 'وجبات', 'label_en': 'Meals'},
                     {'value': 'accommodation', 'label_ar': 'إقامة', 'label_en': 'Accommodation'},
                     {'value': 'supplies', 'label_ar': 'مستلزمات عمل', 'label_en': 'Work Supplies'},
                     {'value': 'other', 'label_ar': 'أخرى', 'label_en': 'Other'},
                 ]},
                {'key': 'details', 'label_ar': 'تفاصيل المصروفات', 'label_en': 'Expense Details', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'بدل مأمورية',
        'name_en': 'Mission Allowance',
        'category_key': 'مالية',
        'description': 'طلب بدل مأمورية أو سفر',
        'description_en': 'Request mission or travel allowance',
        'requires_date_range': True,
        'requires_amount': True,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 4,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'start_date', 'label_ar': 'تاريخ البداية', 'label_en': 'Start Date', 'type': 'date', 'required': True},
                {'key': 'end_date', 'label_ar': 'تاريخ النهاية', 'label_en': 'End Date', 'type': 'date', 'required': True},
                {'key': 'destination', 'label_ar': 'الوجهة', 'label_en': 'Destination', 'type': 'text', 'required': True},
                {'key': 'amount', 'label_ar': 'المبلغ المطلوب', 'label_en': 'Requested Amount', 'type': 'number', 'required': True},
                {'key': 'purpose', 'label_ar': 'الغرض', 'label_en': 'Purpose', 'type': 'textarea', 'required': True},
            ]
        }
    },

    # ═══════════════════════════════════════
    # موارد بشرية
    # ═══════════════════════════════════════
    {
        'name': 'خطاب تعريف',
        'name_en': 'Employment Certificate',
        'category_key': 'موارد بشرية',
        'description': 'طلب خطاب يثبت العمل في الشركة',
        'description_en': 'Request an employment verification letter',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 1,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'target_entity', 'label_ar': 'الجهة الموجه إليها', 'label_en': 'Addressed To', 'type': 'text', 'required': True},
                {'key': 'purpose', 'label_ar': 'الغرض من الخطاب', 'label_en': 'Letter Purpose', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'bank', 'label_ar': 'بنك', 'label_en': 'Bank'},
                     {'value': 'embassy', 'label_ar': 'سفارة', 'label_en': 'Embassy'},
                     {'value': 'government', 'label_ar': 'جهة حكومية', 'label_en': 'Government Entity'},
                     {'value': 'other', 'label_ar': 'أخرى', 'label_en': 'Other'},
                 ]},
                {'key': 'language', 'label_ar': 'لغة الخطاب', 'label_en': 'Letter Language', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'ar', 'label_ar': 'عربي', 'label_en': 'Arabic'},
                     {'value': 'en', 'label_ar': 'إنجليزي', 'label_en': 'English'},
                     {'value': 'both', 'label_ar': 'عربي وإنجليزي', 'label_en': 'Both'},
                 ]},
            ]
        }
    },
    {
        'name': 'خطاب تعريف مرتب',
        'name_en': 'Salary Certificate',
        'category_key': 'موارد بشرية',
        'description': 'طلب خطاب يوضح الراتب',
        'description_en': 'Request a salary verification letter',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 2,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'target_entity', 'label_ar': 'الجهة الموجه إليها', 'label_en': 'Addressed To', 'type': 'text', 'required': True},
                {'key': 'purpose', 'label_ar': 'الغرض', 'label_en': 'Purpose', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'bank_loan', 'label_ar': 'قرض بنكي', 'label_en': 'Bank Loan'},
                     {'value': 'mortgage', 'label_ar': 'رهن عقاري', 'label_en': 'Mortgage'},
                     {'value': 'embassy', 'label_ar': 'سفارة', 'label_en': 'Embassy'},
                     {'value': 'other', 'label_ar': 'أخرى', 'label_en': 'Other'},
                 ]},
                {'key': 'include_allowances', 'label_ar': 'يشمل البدلات؟', 'label_en': 'Include Allowances?', 'type': 'boolean', 'required': False},
            ]
        }
    },
    {
        'name': 'تحديث بيانات شخصية',
        'name_en': 'Update Personal Info',
        'category_key': 'موارد بشرية',
        'description': 'طلب تعديل البيانات الشخصية في ملف الموظف',
        'description_en': 'Request to update personal information',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': True,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 3,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'field_to_update', 'label_ar': 'الحقل المراد تعديله', 'label_en': 'Field to Update', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'phone', 'label_ar': 'رقم الهاتف', 'label_en': 'Phone Number'},
                     {'value': 'address', 'label_ar': 'العنوان', 'label_en': 'Address'},
                     {'value': 'marital_status', 'label_ar': 'الحالة الاجتماعية', 'label_en': 'Marital Status'},
                     {'value': 'emergency_contact', 'label_ar': 'جهة الطوارئ', 'label_en': 'Emergency Contact'},
                     {'value': 'national_id', 'label_ar': 'الرقم القومي', 'label_en': 'National ID'},
                     {'value': 'other', 'label_ar': 'أخرى', 'label_en': 'Other'},
                 ]},
                {'key': 'new_value', 'label_ar': 'القيمة الجديدة', 'label_en': 'New Value', 'type': 'text', 'required': True},
                {'key': 'reason', 'label_ar': 'السبب', 'label_en': 'Reason', 'type': 'textarea', 'required': False},
            ]
        }
    },
    {
        'name': 'تحديث بيانات بنكية',
        'name_en': 'Update Bank Info',
        'category_key': 'موارد بشرية',
        'description': 'طلب تعديل بيانات الحساب البنكي',
        'description_en': 'Request to update bank account details',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': True,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 4,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'bank_name', 'label_ar': 'اسم البنك', 'label_en': 'Bank Name', 'type': 'text', 'required': True},
                {'key': 'account_number', 'label_ar': 'رقم الحساب', 'label_en': 'Account Number', 'type': 'text', 'required': True},
                {'key': 'iban', 'label_ar': 'رقم الآيبان (IBAN)', 'label_en': 'IBAN', 'type': 'text', 'required': False},
                {'key': 'account_name', 'label_ar': 'اسم صاحب الحساب', 'label_en': 'Account Holder Name', 'type': 'text', 'required': True},
            ]
        }
    },

    # ═══════════════════════════════════════
    # إدارية وتشغيلية
    # ═══════════════════════════════════════
    {
        'name': 'طلب عهدة',
        'name_en': 'Equipment Request',
        'category_key': 'إدارية وتشغيلية',
        'description': 'طلب عهدة معدات أو أدوات عمل',
        'description_en': 'Request work equipment or tools',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 1,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'equipment_type', 'label_ar': 'نوع العهدة', 'label_en': 'Equipment Type', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'laptop', 'label_ar': 'لاب توب', 'label_en': 'Laptop'},
                     {'value': 'mobile', 'label_ar': 'موبايل', 'label_en': 'Mobile Phone'},
                     {'value': 'sim_card', 'label_ar': 'شريحة اتصال', 'label_en': 'SIM Card'},
                     {'value': 'printer', 'label_ar': 'طابعة', 'label_en': 'Printer'},
                     {'value': 'vehicle', 'label_ar': 'سيارة', 'label_en': 'Vehicle'},
                     {'value': 'other', 'label_ar': 'أخرى', 'label_en': 'Other'},
                 ]},
                {'key': 'quantity', 'label_ar': 'الكمية', 'label_en': 'Quantity', 'type': 'number', 'required': True},
                {'key': 'purpose', 'label_ar': 'الغرض', 'label_en': 'Purpose', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'طلب صلاحية نظام',
        'name_en': 'System Access Request',
        'category_key': 'إدارية وتشغيلية',
        'description': 'طلب صلاحية دخول على نظام أو برنامج',
        'description_en': 'Request system or software access',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 2,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'system_name', 'label_ar': 'اسم النظام / البرنامج', 'label_en': 'System / Software Name', 'type': 'text', 'required': True},
                {'key': 'access_level', 'label_ar': 'مستوى الصلاحية', 'label_en': 'Access Level', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'read', 'label_ar': 'قراءة فقط', 'label_en': 'Read Only'},
                     {'value': 'edit', 'label_ar': 'قراءة وتعديل', 'label_en': 'Read & Edit'},
                     {'value': 'full', 'label_ar': 'صلاحية كاملة', 'label_en': 'Full Access'},
                 ]},
                {'key': 'reason', 'label_ar': 'سبب الحاجة للصلاحية', 'label_en': 'Reason for Access', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'طلب صيانة',
        'name_en': 'Maintenance Request',
        'category_key': 'إدارية وتشغيلية',
        'description': 'طلب إصلاح جهاز أو معدة',
        'description_en': 'Request repair or maintenance',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 3,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'equipment', 'label_ar': 'الجهاز / المعدة', 'label_en': 'Equipment', 'type': 'text', 'required': True},
                {'key': 'issue', 'label_ar': 'وصف المشكلة', 'label_en': 'Problem Description', 'type': 'textarea', 'required': True},
                {'key': 'urgency', 'label_ar': 'مستوى الأولوية', 'label_en': 'Priority Level', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'low', 'label_ar': 'منخفض', 'label_en': 'Low'},
                     {'value': 'medium', 'label_ar': 'متوسط', 'label_en': 'Medium'},
                     {'value': 'high', 'label_ar': 'عالي', 'label_en': 'High'},
                     {'value': 'urgent', 'label_ar': 'عاجل جداً', 'label_en': 'Urgent'},
                 ]},
            ]
        }
    },
    {
        'name': 'طلب مقابلة إدارية',
        'name_en': 'Meeting Request',
        'category_key': 'إدارية وتشغيلية',
        'description': 'طلب مقابلة مع المدير أو HR',
        'description_en': 'Request a meeting with manager or HR',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 4,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'meeting_with', 'label_ar': 'المقابلة مع', 'label_en': 'Meeting With', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'direct_manager', 'label_ar': 'المدير المباشر', 'label_en': 'Direct Manager'},
                     {'value': 'hr', 'label_ar': 'الموارد البشرية', 'label_en': 'HR'},
                     {'value': 'company_admin', 'label_ar': 'صاحب الشركة', 'label_en': 'Company Admin'},
                 ]},
                {'key': 'preferred_date', 'label_ar': 'التاريخ المفضل', 'label_en': 'Preferred Date', 'type': 'date', 'required': True},
                {'key': 'topic', 'label_ar': 'موضوع المقابلة', 'label_en': 'Meeting Topic', 'type': 'textarea', 'required': True},
            ]
        }
    },

    # ═══════════════════════════════════════
    # عام
    # ═══════════════════════════════════════
    {
        'name': 'طلب عام',
        'name_en': 'General Request',
        'category_key': 'عام',
        'description': 'أي طلب لا يندرج تحت الفئات الأخرى',
        'description_en': 'Any request not covered by other categories',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 1,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'request_details', 'label_ar': 'تفاصيل الطلب', 'label_en': 'Request Details', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'شكوى',
        'name_en': 'Complaint',
        'category_key': 'عام',
        'description': 'تقديم شكوى رسمية',
        'description_en': 'Submit a formal complaint',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': True,
        'permission_kind': 'none',
        'order': 2,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'complaint_against', 'label_ar': 'الشكوى ضد', 'label_en': 'Complaint Against', 'type': 'text', 'required': False},
                {'key': 'incident_date', 'label_ar': 'تاريخ الحادثة', 'label_en': 'Incident Date', 'type': 'date', 'required': False},
                {'key': 'complaint_details', 'label_ar': 'تفاصيل الشكوى', 'label_en': 'Complaint Details', 'type': 'textarea', 'required': True},
            ]
        }
    },
    {
        'name': 'اقتراح',
        'name_en': 'Suggestion',
        'category_key': 'عام',
        'description': 'تقديم اقتراح لتحسين بيئة العمل',
        'description_en': 'Submit a suggestion to improve the workplace',
        'requires_date_range': False,
        'requires_amount': False,
        'requires_document': False,
        'requires_approval': False,
        'permission_kind': 'none',
        'order': 3,
        'is_active': True,
        'form_schema': {
            'fields': [
                {'key': 'suggestion_area', 'label_ar': 'مجال الاقتراح', 'label_en': 'Suggestion Area', 'type': 'select', 'required': True,
                 'options': [
                     {'value': 'work_environment', 'label_ar': 'بيئة العمل', 'label_en': 'Work Environment'},
                     {'value': 'processes', 'label_ar': 'الإجراءات', 'label_en': 'Processes'},
                     {'value': 'benefits', 'label_ar': 'المزايا', 'label_en': 'Benefits'},
                     {'value': 'training', 'label_ar': 'التدريب', 'label_en': 'Training'},
                     {'value': 'other', 'label_ar': 'أخرى', 'label_en': 'Other'},
                 ]},
                {'key': 'suggestion', 'label_ar': 'الاقتراح', 'label_en': 'Suggestion', 'type': 'textarea', 'required': True},
                {'key': 'expected_benefit', 'label_ar': 'الفائدة المتوقعة', 'label_en': 'Expected Benefit', 'type': 'textarea', 'required': False},
            ]
        }
    },
]
