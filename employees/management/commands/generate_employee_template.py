"""
Management Command: generate_employee_template
ينشئ شيت إكسيل احترافي لاستيراد الموظفين
"""
from django.core.management.base import BaseCommand
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side
)
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter


class Command(BaseCommand):
    help = 'ينشئ شيت Excel لاستيراد الموظفين'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='/var/www/motionhr/media/employee_import_template.xlsx',
            help='مسار حفظ الملف'
        )

    def handle(self, *args, **options):
        output_path = options['output']
        wb = Workbook()

        self._create_instructions_sheet(wb)
        self._create_employees_sheet(wb)
        self._create_lists_sheet(wb)

        wb.save(output_path)
        self.stdout.write(self.style.SUCCESS(
            f'تم إنشاء الشيت بنجاح: {output_path}'
        ))

    def _create_instructions_sheet(self, wb):
        ws = wb.active
        ws.title = 'تعليمات'

        header_fill = PatternFill(start_color='1565C0', end_color='1565C0', fill_type='solid')
        header_font = Font(color='FFFFFF', bold=True, size=12)
        bold_font = Font(bold=True, size=11)
        red_font = Font(color='C62828', bold=True)
        green_font = Font(color='1B5E20', bold=True)

        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 60

        ws['A1'] = 'نظام استيراد الموظفين - MotionHR'
        ws['A1'].fill = header_fill
        ws['A1'].font = header_font
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.merge_cells('A1:B1')
        ws.row_dimensions[1].height = 35

        instructions = [
            ('', ''),
            ('قواعد عامة', ''),
            ('نوع العملية (operation_type)', 'new = موظف جديد | update = تحديث موظف حالي'),
            ('الخانات بالنجمة (*)', 'إجبارية ولا يمكن رفع الشيت بدونها'),
            ('الخانات بدون نجمة', 'اختيارية'),
            ('', ''),
            ('تنسيقات مهمة', ''),
            ('أعمدة النصوص', 'موبايل، رقم قومي، IBAN، باسبور، كود موظف، باسورد'),
            ('سبب Text في الموبايل', 'عشان الصفر في الشمال ما يطيرش'),
            ('IBAN', 'يبدأ بحروف زي EG في مصر، فلازم يبقى Text مش رقم'),
            ('الباسبور', 'يمكن يحتوي على حروف وأرقام، فلازم يبقى Text'),
            ('', ''),
            ('أرصدة الإجازات', ''),
            ('entitled', 'الرصيد المستحق في السنة دي'),
            ('used_before_system', 'الأيام اللي اتاخدت قبل تشغيل السيستم'),
            ('carry_forward', 'الرصيد المرحل من سنة سابقة'),
            ('المتبقي', 'السيستم بيحسبه تلقائي = entitled + carry_forward - used'),
            ('', ''),
            ('تعريف الموظف في update', ''),
            ('employee_code', 'كود الموظف في السيستم (إجباري في التحديث)'),
            ('national_id', 'الرقم القومي كبديل إذا لم يتوفر الكود'),
        ]

        for row_idx, (col_a, col_b) in enumerate(instructions, start=2):
            ws[f'A{row_idx}'] = col_a
            ws[f'B{row_idx}'] = col_b

            if col_b == '' and col_a != '':
                ws[f'A{row_idx}'].font = bold_font
                ws[f'A{row_idx}'].fill = PatternFill(
                    start_color='E3F2FD', end_color='E3F2FD', fill_type='solid')
                ws.merge_cells(f'A{row_idx}:B{row_idx}')
            elif '(*)' in col_a or 'إجباري' in col_b:
                ws[f'A{row_idx}'].font = red_font
            elif 'اختيار' in col_b:
                ws[f'A{row_idx}'].font = green_font

    def _create_employees_sheet(self, wb):
        ws = wb.create_sheet('الموظفين')

        columns = [
            # العملية
            ('operation_type', 'نوع العملية *', True, 'list', 'new,update', 15),
            ('employee_code', 'كود الموظف', False, None, None, 15),
            ('temporary_password', 'الباسورد المؤقتة *', True, None, None, 20),

            # الشخصية
            ('first_name_ar', 'الاسم الأول عربي *', True, None, None, 20),
            ('middle_name_ar', 'الاسم الأوسط عربي', False, None, None, 20),
            ('last_name_ar', 'الاسم الأخير عربي *', True, None, None, 20),
            ('first_name_en', 'الاسم الأول إنجليزي *', True, None, None, 20),
            ('last_name_en', 'الاسم الأخير إنجليزي *', True, None, None, 20),
            ('national_id', 'الرقم القومي *', True, None, None, 20),
            ('passport_number', 'رقم الباسبور', False, None, None, 18),
            ('birth_date', 'تاريخ الميلاد * (YYYY-MM-DD)', True, None, None, 22),
            ('gender', 'النوع *', True, 'list', 'القوائم!$B$2:$B$3', 12),
            ('marital_status', 'الحالة الاجتماعية', False, 'list', 'القوائم!$C$2:$C$5', 18),
            ('religion', 'الديانة', False, 'list', 'القوائم!$D$2:$D$4', 12),
            ('nationality', 'الجنسية', False, None, None, 15),
            ('language', 'اللغة', False, 'list', 'القوائم!$E$2:$E$3', 10),

            # التواصل
            ('country_code', 'كود الدولة', False, None, None, 12),
            ('phone', 'الموبايل * (Text)', True, None, None, 18),
            ('phone2', 'موبايل إضافي', False, None, None, 18),
            ('email', 'البريد الإلكتروني', False, None, None, 25),
            ('address', 'العنوان', False, None, None, 30),
            ('city', 'المدينة', False, None, None, 15),
            ('emergency_contact_name', 'اسم جهة الطوارئ', False, None, None, 22),
            ('emergency_contact_relation', 'صلة القرابة', False, None, None, 15),
            ('emergency_contact_phone', 'موبايل الطوارئ (Text)', False, None, None, 20),

            # الوظيفة
            ('branch_name', 'الفرع *', True, 'list', 'القوائم!$F$2:$F$100', 20),
            ('department_name', 'القسم *', True, 'list', 'القوائم!$G$2:$G$100', 20),
            ('job_title_name', 'المسمى الوظيفي *', True, 'list', 'القوائم!$H$2:$H$100', 22),
            ('direct_manager_code', 'كود المدير المباشر', False, None, None, 20),
            ('hire_date', 'تاريخ التعيين * (YYYY-MM-DD)', True, None, None, 25),
            ('attendance_mode', 'نمط الحضور *', True, 'list', 'القوائم!$I$2:$I$6', 18),

            # العقد
            ('contract_type', 'نوع العقد *', True, 'list', 'القوائم!$J$2:$J$7', 18),
            ('contract_start_date', 'بداية العقد (YYYY-MM-DD)', False, None, None, 22),
            ('contract_end_date', 'نهاية العقد (YYYY-MM-DD)', False, None, None, 22),
            ('contract_duration_months', 'مدة العقد بالشهور', False, None, None, 20),
            ('probation_months', 'فترة التجربة بالشهور', False, None, None, 20),

            # التأمين
            ('has_insurance', 'مؤمن عليه', False, 'list', 'نعم,لا', 12),
            ('insurance_number', 'رقم التأمين (Text)', False, None, None, 18),

            # الماليات
            ('basic_salary', 'المرتب الأساسي', False, None, None, 18),
            ('currency', 'العملة', False, 'list', 'القوائم!$K$2:$K$7', 10),
            ('salary_payment_method', 'طريقة القبض *', True, 'list', 'القوائم!$L$2:$L$5', 18),
            ('bank_name', 'اسم البنك', False, None, None, 20),
            ('bank_account', 'رقم الحساب (Text)', False, None, None, 20),
            ('bank_account_holder_name', 'اسم صاحب الحساب', False, None, None, 22),
            ('iban', 'IBAN (Text - EG...)', False, None, None, 30),
            ('instapay_transfer_id', 'رقم إنستا باي (Text)', False, None, None, 22),
            ('wallet_transfer_number', 'رقم المحفظة (Text)', False, None, None, 22),
            ('wallet_provider', 'مزود المحفظة', False, 'list', 'القوائم!$M$2:$M$7', 18),

            # أرصدة الإجازات
            ('annual_entitled', 'السنوية - المستحق', False, None, None, 20),
            ('annual_used_before_system', 'السنوية - المستنفذ', False, None, None, 22),
            ('annual_carry_forward', 'السنوية - مرحل', False, None, None, 18),
            ('sick_entitled', 'المرضية - المستحق', False, None, None, 20),
            ('sick_used_before_system', 'المرضية - المستنفذ', False, None, None, 22),
            ('sick_carry_forward', 'المرضية - مرحل', False, None, None, 18),
            ('emergency_entitled', 'الطارئة - المستحق', False, None, None, 20),
            ('emergency_used_before_system', 'الطارئة - المستنفذ', False, None, None, 22),
            ('emergency_carry_forward', 'الطارئة - مرحل', False, None, None, 18),
            ('maternity_entitled', 'الأمومة - المستحق', False, None, None, 20),
            ('maternity_used_before_system', 'الأمومة - المستنفذ', False, None, None, 22),
            ('maternity_carry_forward', 'الأمومة - مرحل', False, None, None, 18),
            ('paternity_entitled', 'الأبوة - المستحق', False, None, None, 20),
            ('paternity_used_before_system', 'الأبوة - المستنفذ', False, None, None, 22),
            ('paternity_carry_forward', 'الأبوة - مرحل', False, None, None, 18),
            ('unpaid_entitled', 'بدون مرتب - المستحق', False, None, None, 22),
            ('unpaid_used_before_system', 'بدون مرتب - المستنفذ', False, None, None, 24),
            ('unpaid_carry_forward', 'بدون مرتب - مرحل', False, None, None, 20),
        ]

        # ألوان
        required_fill = PatternFill(start_color='FFCDD2', end_color='FFCDD2', fill_type='solid')
        optional_fill = PatternFill(start_color='E8F5E9', end_color='E8F5E9', fill_type='solid')
        header_font = Font(bold=True, size=10)
        center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        thin = Side(style='thin')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # section headers
        sections = [
            (1, 3, 'بيانات العملية', 'FFE082'),
            (4, 16, 'البيانات الشخصية', 'CE93D8'),
            (17, 24, 'التواصل', '80DEEA'),
            (25, 31, 'بيانات الوظيفة', '90CAF9'),
            (32, 36, 'العقد', 'A5D6A7'),
            (37, 38, 'التأمين', 'FFCC80'),
            (39, 48, 'الماليات', 'F48FB1'),
            (49, 67, 'أرصدة الإجازات', 'B2DFDB'),
        ]

        # Row 1: section headers
        for start_col, end_col, label, color in sections:
            ws.merge_cells(
                start_row=1, start_column=start_col,
                end_row=1, end_column=end_col
            )
            cell = ws.cell(row=1, column=start_col, value=label)
            cell.fill = PatternFill(start_color=color, end_color=color, fill_type='solid')
            cell.font = Font(bold=True, size=10)
            cell.alignment = center
            cell.border = border

        # Row 2: column names
        # Row 3: column keys
        for col_idx, (key, label, required, val_type, val_formula, width) in enumerate(columns, start=1):
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width

            # header label
            cell = ws.cell(row=2, column=col_idx, value=label)
            cell.fill = required_fill if required else optional_fill
            cell.font = header_font
            cell.alignment = center
            cell.border = border

            # key
            key_cell = ws.cell(row=3, column=col_idx, value=key)
            key_cell.font = Font(size=8, italic=True, color='757575')
            key_cell.alignment = center
            key_cell.border = border

            # Data validation
            if val_type == 'list' and val_formula:
                if val_formula.startswith('القوائم') or val_formula.startswith('new') or val_formula.startswith('نعم'):
                    if val_formula.startswith('القوائم'):
                        dv = DataValidation(
                            type='list',
                            formula1=f'={val_formula}',
                            allow_blank=not required,
                        )
                    else:
                        dv = DataValidation(
                            type='list',
                            formula1=f'"{val_formula}"',
                            allow_blank=not required,
                        )
                    dv.sqref = f'{col_letter}4:{col_letter}10000'
                    ws.add_data_validation(dv)

            # Text format for specific columns
            text_columns = [
                'employee_code', 'temporary_password', 'national_id',
                'passport_number', 'phone', 'phone2', 'emergency_contact_phone',
                'insurance_number', 'bank_account', 'iban',
                'instapay_transfer_id', 'wallet_transfer_number',
            ]
            if key in text_columns:
                for row in range(4, 10001):
                    ws.cell(row=row, column=col_idx).number_format = '@'

        ws.row_dimensions[1].height = 30
        ws.row_dimensions[2].height = 45
        ws.row_dimensions[3].height = 20
        ws.freeze_panes = 'A4'

    def _create_lists_sheet(self, wb):
        ws = wb.create_sheet('القوائم')

        from companies.models import Branch, Department
        from employees.models import JobTitle

        header_fill = PatternFill(start_color='455A64', end_color='455A64', fill_type='solid')
        header_font = Font(color='FFFFFF', bold=True)
        center = Alignment(horizontal='center')

        lists = {
            'A': ('operation_type', ['new', 'update']),
            'B': ('gender', ['male', 'female']),
            'C': ('marital_status', ['single', 'married', 'divorced', 'widowed']),
            'D': ('religion', ['muslim', 'christian', 'other']),
            'E': ('language', ['ar', 'en']),
            'F': ('branch_name', []),
            'G': ('department_name', []),
            'H': ('job_title_name', []),
            'I': ('attendance_mode', [
                'fixed_shift', 'flexible_hours',
                'field_worker', 'remote', 'rotating'
            ]),
            'J': ('contract_type', [
                'permanent', 'temporary', 'training',
                'freelance', 'part_time', 'consultant'
            ]),
            'K': ('currency', ['EGP', 'USD', 'SAR', 'AED', 'KWD', 'QAR']),
            'L': ('salary_payment_method', ['cash', 'bank', 'instapay', 'wallet']),
            'M': ('wallet_provider', [
                'vodafone_cash', 'orange_money',
                'etisalat_cash', 'we_pay', 'fawry', 'other'
            ]),
        }

        # Populate dynamic lists from DB
        try:
            lists['F'] = ('branch_name', list(Branch.objects.values_list('name_ar', flat=True)))
        except Exception:
            pass
        try:
            lists['G'] = ('department_name', list(Department.objects.values_list('name_ar', flat=True)))
        except Exception:
            pass
        try:
            lists['H'] = ('job_title_name', list(JobTitle.objects.values_list('name_ar', flat=True)))
        except Exception:
            pass

        for col_letter, (header, values) in lists.items():
            col_idx = ord(col_letter) - ord('A') + 1
            ws.column_dimensions[col_letter].width = 25

            header_cell = ws.cell(row=1, column=col_idx, value=header)
            header_cell.fill = header_fill
            header_cell.font = header_font
            header_cell.alignment = center

            for row_idx, value in enumerate(values, start=2):
                ws.cell(row=row_idx, column=col_idx, value=value)

        ws.sheet_state = 'hidden'
