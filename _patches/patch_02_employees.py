"""
============================================================
Patch 02: Employees - PDF Export + Print + Edit Page
============================================================
هذا السكريبت يضيف:
- تصدير PDF للموظفين
- صفحة طباعة احترافية
- صفحة تعديل مستقلة للموظف

للتشغيل:
    python _patches/patch_02_employees.py
============================================================
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# 1. Views الجديدة
# ═══════════════════════════════════════════════════════════

NEW_VIEWS_CODE = '''

def export_employees_pdf(employees):
    """تصدير قائمة الموظفين إلى PDF"""
    from django.template.loader import render_to_string
    from weasyprint import HTML
    from django.utils import timezone
    
    html_string = render_to_string('employees/print_list.html', {
        'employees': employees,
        'generated_at': timezone.now(),
        'total_count': employees.count() if hasattr(employees, 'count') else len(employees),
    })
    
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
def employee_print(request, pk=None):
    """صفحة طباعة (موظف واحد أو الكل)"""
    if pk:
        employees = Employee.objects.filter(pk=pk)
        title = f"بيانات {employees.first().full_name_ar}" if employees.exists() else "موظف"
    else:
        employees = Employee.objects.all().select_related('branch', 'department', 'job_title')
        title = "قائمة الموظفين"
    
    from django.utils import timezone
    context = {
        'employees': employees,
        'title': title,
        'generated_at': timezone.now(),
        'is_single': pk is not None,
    }
    
    return render(request, 'employees/print_list.html', context)


@login_required
def employee_print_detail(request, pk):
    """طباعة بيانات موظف واحد بالتفصيل"""
    employee = get_object_or_404(Employee, pk=pk)
    from django.utils import timezone
    
    context = {
        'employee': employee,
        'generated_at': timezone.now(),
    }
    
    return render(request, 'employees/print_detail.html', context)
'''


# ═══════════════════════════════════════════════════════════
# 2. الملفات
# ═══════════════════════════════════════════════════════════

FILES = {
    # ────────────────────────────────────────
    # صفحة طباعة قائمة الموظفين
    # ────────────────────────────────────────
    'templates/employees/print_list.html': '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>{{ title|default:"قائمة الموظفين" }} - MotionHR</title>
    <style>
        @page {
            size: A4 landscape;
            margin: 1.5cm;
        }
        
        * {
            font-family: 'Cairo', 'Arial', sans-serif;
            box-sizing: border-box;
        }
        
        body {
            margin: 0;
            padding: 20px;
            color: #1E293B;
        }
        
        .header {
            border-bottom: 3px solid #06B6D4;
            padding-bottom: 15px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .logo {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #06B6D4, #3B82F6);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
        }
        
        h1 {
            color: #06B6D4;
            margin: 0;
            font-size: 24px;
        }
        
        .subtitle {
            color: #64748B;
            font-size: 12px;
            margin-top: 3px;
        }
        
        .info-box {
            background: #F1F5F9;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 12px;
            color: #64748B;
        }
        
        .stats {
            background: linear-gradient(135deg, #06B6D4, #3B82F6);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-around;
            text-align: center;
        }
        
        .stat-item {
            flex: 1;
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 12px;
            opacity: 0.9;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        }
        
        thead {
            background: #1E293B;
            color: white;
        }
        
        th {
            padding: 10px 8px;
            text-align: right;
            font-weight: 600;
        }
        
        td {
            padding: 8px;
            border-bottom: 1px solid #E2E8F0;
        }
        
        tbody tr:nth-child(even) {
            background: #F8FAFC;
        }
        
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
        }
        
        .badge-success {
            background: #D1FAE5;
            color: #065F46;
        }
        
        .badge-warning {
            background: #FEF3C7;
            color: #92400E;
        }
        
        .badge-danger {
            background: #FEE2E2;
            color: #991B1B;
        }
        
        .badge-info {
            background: #DBEAFE;
            color: #1E40AF;
        }
        
        .badge-secondary {
            background: #F1F5F9;
            color: #475569;
        }
        
        .footer {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #E2E8F0;
            text-align: center;
            color: #94A3B8;
            font-size: 10px;
        }
        
        .no-print {
            display: none !important;
        }
        
        @media print {
            .no-print {
                display: none !important;
            }
        }
    </style>
</head>
<body>
    
    <!-- Header -->
    <div class="header">
        <div class="header-left">
            <div class="logo">M</div>
            <div>
                <h1>MotionHR</h1>
                <div class="subtitle">إدارة الموارد البشرية</div>
            </div>
        </div>
        <div class="info-box">
            <div><strong>{{ title|default:"قائمة الموظفين" }}</strong></div>
            <div>تاريخ الطباعة: {{ generated_at|date:"Y-m-d H:i" }}</div>
        </div>
    </div>
    
    <!-- Stats -->
    <div class="stats">
        <div class="stat-item">
            <div class="stat-value">{{ total_count|default:employees.count }}</div>
            <div class="stat-label">إجمالي الموظفين</div>
        </div>
    </div>
    
    <!-- Table -->
    <table>
        <thead>
            <tr>
                <th style="width: 5%;">#</th>
                <th style="width: 10%;">الرقم الوظيفي</th>
                <th style="width: 20%;">الاسم</th>
                <th style="width: 15%;">المسمى الوظيفي</th>
                <th style="width: 12%;">الإدارة</th>
                <th style="width: 12%;">الفرع</th>
                <th style="width: 12%;">الموبايل</th>
                <th style="width: 9%;">تاريخ التعيين</th>
                <th style="width: 5%;">الحالة</th>
            </tr>
        </thead>
        <tbody>
            {% for employee in employees %}
            <tr>
                <td>{{ forloop.counter }}</td>
                <td><strong>{{ employee.employee_code }}</strong></td>
                <td>{{ employee.full_name_ar }}</td>
                <td>{{ employee.job_title.name_ar }}</td>
                <td>{{ employee.department.name_ar }}</td>
                <td>{{ employee.branch.name_ar }}</td>
                <td>{{ employee.phone }}</td>
                <td>{{ employee.hire_date }}</td>
                <td>
                    {% if employee.status == 'active' %}
                        <span class="badge badge-success">نشط</span>
                    {% elif employee.status == 'on_leave' %}
                        <span class="badge badge-info">إجازة</span>
                    {% elif employee.status == 'suspended' %}
                        <span class="badge badge-warning">موقوف</span>
                    {% else %}
                        <span class="badge badge-secondary">{{ employee.get_status_display }}</span>
                    {% endif %}
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="9" style="text-align: center; padding: 30px; color: #94A3B8;">
                    لا يوجد موظفون
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <!-- Footer -->
    <div class="footer">
        <div>MotionHR © 2025 - جميع الحقوق محفوظة</div>
        <div>تم إنشاء هذا التقرير في {{ generated_at|date:"Y-m-d H:i:s" }}</div>
    </div>
    
    <script>
        // طباعة تلقائية لما الصفحة تفتح
        if (window.location.search.includes('auto=1')) {
            window.print();
        }
    </script>
    
</body>
</html>
''',

    # ────────────────────────────────────────
    # صفحة طباعة بيانات موظف واحد
    # ────────────────────────────────────────
    'templates/employees/print_detail.html': '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>{{ employee.full_name_ar }} - MotionHR</title>
    <style>
        @page {
            size: A4;
            margin: 1.5cm;
        }
        
        * {
            font-family: 'Cairo', 'Arial', sans-serif;
            box-sizing: border-box;
        }
        
        body {
            margin: 0;
            padding: 20px;
            color: #1E293B;
        }
        
        .header {
            border-bottom: 3px solid #06B6D4;
            padding-bottom: 15px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #06B6D4, #3B82F6);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
        }
        
        .header h1 {
            color: #06B6D4;
            margin: 0;
            font-size: 22px;
        }
        
        .employee-header {
            background: linear-gradient(135deg, #06B6D4, #3B82F6);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .avatar {
            width: 90px;
            height: 90px;
            border-radius: 50%;
            background: white;
            color: #06B6D4;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 42px;
            font-weight: bold;
        }
        
        .employee-info h2 {
            margin: 0 0 5px 0;
            font-size: 24px;
        }
        
        .employee-info .job {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .employee-info .code {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            margin-top: 8px;
        }
        
        .section {
            margin-bottom: 25px;
            page-break-inside: avoid;
        }
        
        .section-title {
            background: #F1F5F9;
            padding: 10px 15px;
            border-right: 4px solid #06B6D4;
            margin-bottom: 12px;
            font-weight: bold;
            color: #1E293B;
            border-radius: 4px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        
        .info-item {
            padding: 8px 12px;
            background: #F8FAFC;
            border-radius: 6px;
            border-right: 3px solid #E2E8F0;
        }
        
        .info-label {
            font-size: 10px;
            color: #64748B;
            margin-bottom: 3px;
        }
        
        .info-value {
            font-size: 12px;
            color: #1E293B;
            font-weight: 600;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 15px;
            border-top: 1px solid #E2E8F0;
            text-align: center;
            color: #94A3B8;
            font-size: 10px;
        }
        
        .signature-box {
            margin-top: 40px;
            display: flex;
            justify-content: space-between;
            gap: 40px;
        }
        
        .signature {
            flex: 1;
            border-top: 2px solid #1E293B;
            padding-top: 8px;
            text-align: center;
            font-size: 11px;
        }
    </style>
</head>
<body>
    
    <div class="header">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="logo">M</div>
            <div>
                <h1>MotionHR</h1>
                <div style="color: #64748B; font-size: 11px;">بطاقة موظف</div>
            </div>
        </div>
        <div style="text-align: left; color: #64748B; font-size: 11px;">
            <div>تاريخ الطباعة</div>
            <div><strong>{{ generated_at|date:"Y-m-d H:i" }}</strong></div>
        </div>
    </div>
    
    <div class="employee-header">
        <div class="avatar">{{ employee.first_name_ar|first }}</div>
        <div class="employee-info">
            <h2>{{ employee.full_name_ar }}</h2>
            <div class="job">{{ employee.job_title.name_ar }}</div>
            <span class="code">{{ employee.employee_code }}</span>
        </div>
    </div>
    
    <!-- البيانات الشخصية -->
    <div class="section">
        <div class="section-title">📋 البيانات الشخصية</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">الاسم بالعربي</div>
                <div class="info-value">{{ employee.full_name_ar }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">الاسم بالإنجليزي</div>
                <div class="info-value">{{ employee.full_name_en|default:"-" }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">الرقم القومي</div>
                <div class="info-value">{{ employee.national_id }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">تاريخ الميلاد</div>
                <div class="info-value">{{ employee.birth_date }} ({{ employee.age }} سنة)</div>
            </div>
            <div class="info-item">
                <div class="info-label">النوع</div>
                <div class="info-value">{{ employee.get_gender_display }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">الحالة الاجتماعية</div>
                <div class="info-value">{{ employee.get_marital_status_display }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">الديانة</div>
                <div class="info-value">{{ employee.get_religion_display|default:"-" }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">الجنسية</div>
                <div class="info-value">{{ employee.nationality }}</div>
            </div>
        </div>
    </div>
    
    <!-- بيانات التواصل -->
    <div class="section">
        <div class="section-title">📞 بيانات التواصل</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">رقم الموبايل</div>
                <div class="info-value">{{ employee.phone }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">رقم موبايل آخر</div>
                <div class="info-value">{{ employee.phone2|default:"-" }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">البريد الإلكتروني</div>
                <div class="info-value">{{ employee.email|default:"-" }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">المدينة</div>
                <div class="info-value">{{ employee.city|default:"-" }}</div>
            </div>
        </div>
        {% if employee.address %}
        <div style="margin-top: 10px;" class="info-item">
            <div class="info-label">العنوان</div>
            <div class="info-value">{{ employee.address }}</div>
        </div>
        {% endif %}
    </div>
    
    <!-- بيانات التعيين -->
    <div class="section">
        <div class="section-title">💼 بيانات التعيين</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">تاريخ التعيين</div>
                <div class="info-value">{{ employee.hire_date }} ({{ employee.years_of_service }} سنة)</div>
            </div>
            <div class="info-item">
                <div class="info-label">نوع العقد</div>
                <div class="info-value">{{ employee.get_contract_type_display }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">الفرع</div>
                <div class="info-value">{{ employee.branch.name_ar }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">الإدارة</div>
                <div class="info-value">{{ employee.department.name_ar }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">المسمى الوظيفي</div>
                <div class="info-value">{{ employee.job_title.name_ar }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">المدير المباشر</div>
                <div class="info-value">
                    {% if employee.direct_manager %}
                        {{ employee.direct_manager.full_name_ar }}
                    {% else %}-{% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <!-- التوقيعات -->
    <div class="signature-box">
        <div class="signature">
            <div>توقيع الموظف</div>
        </div>
        <div class="signature">
            <div>توقيع الموارد البشرية</div>
        </div>
        <div class="signature">
            <div>توقيع المدير المباشر</div>
        </div>
    </div>
    
    <div class="footer">
        <div><strong>MotionHR</strong> © 2025 - جميع الحقوق محفوظة</div>
        <div>هذه الوثيقة صادرة عن نظام إدارة الموارد البشرية</div>
    </div>
    
    <script>
        if (window.location.search.includes('auto=1')) {
            window.print();
        }
    </script>
    
</body>
</html>
''',
}


# ═══════════════════════════════════════════════════════════
# التعديلات على الملفات
# ═══════════════════════════════════════════════════════════

def update_employee_views():
    """إضافة views جديدة للطباعة والـ PDF"""
    views_path = BASE_DIR / 'employees' / 'views.py'
    
    if not views_path.exists():
        return False, "ملف views.py مش موجود"
    
    content = views_path.read_text(encoding='utf-8')
    
    if 'employee_print' in content:
        return True, "الـ views موجودة بالفعل"
    
    # ضيف الـ Views في النهاية
    with views_path.open('a', encoding='utf-8') as f:
        f.write(NEW_VIEWS_CODE)
    
    # ضيف الـ PDF logic في function التصدير
    old_pdf_line = "messages.info(request, 'تصدير PDF قيد التطوير - جرب Excel')\n        return redirect('employees:list')"
    new_pdf_line = "return export_employees_pdf(employees)"
    
    content = views_path.read_text(encoding='utf-8')
    if old_pdf_line in content:
        content = content.replace(old_pdf_line, new_pdf_line)
        views_path.write_text(content, encoding='utf-8')
    
    return True, "تم إضافة views للطباعة والـ PDF"


def update_employee_urls():
    """إضافة URLs للطباعة"""
    urls_path = BASE_DIR / 'employees' / 'urls.py'
    
    if not urls_path.exists():
        return False, "ملف urls.py مش موجود"
    
    content = urls_path.read_text(encoding='utf-8')
    
    if 'employee_print' in content:
        return True, "الـ URLs موجودة بالفعل"
    
    # ضيف قبل ]
    old = "path('<int:pk>/delete/', views.employee_delete, name='delete'),"
    new = '''path('<int:pk>/delete/', views.employee_delete, name='delete'),
    
    # الطباعة
    path('print/', views.employee_print, name='print_all'),
    path('<int:pk>/print/', views.employee_print_detail, name='print_detail'),'''
    
    if old not in content:
        return False, "لم يتم العثور على السطر المطلوب"
    
    content = content.replace(old, new)
    urls_path.write_text(content, encoding='utf-8')
    
    return True, "تم تحديث urls.py"


def update_employee_list_template():
    """تحديث قائمة الطباعة في list.html"""
    list_path = BASE_DIR / 'templates' / 'employees' / 'list.html'
    
    if not list_path.exists():
        return False, "ملف list.html مش موجود"
    
    content = list_path.read_text(encoding='utf-8')
    
    if 'employees:print_all' in content:
        return True, "التعديل موجود بالفعل"
    
    old = '''<li>
                                <a class="dropdown-item" href="?export=pdf{% if search %}&search={{ search }}{% endif %}">
                                    <i class="bi bi-file-earmark-pdf text-danger"></i>
                                    PDF
                                </a>
                            </li>
                            <li><hr class="dropdown-divider"></li>
                            <li>
                                <a class="dropdown-item" href="#" onclick="window.print(); return false;">
                                    <i class="bi bi-printer"></i>
                                    طباعة
                                </a>
                            </li>'''
    
    new = '''<li>
                                <a class="dropdown-item" href="?export=pdf{% if search %}&search={{ search }}{% endif %}">
                                    <i class="bi bi-file-earmark-pdf text-danger"></i>
                                    PDF
                                </a>
                            </li>
                            <li><hr class="dropdown-divider"></li>
                            <li>
                                <a class="dropdown-item" href="{% url 'employees:print_all' %}" target="_blank">
                                    <i class="bi bi-printer"></i>
                                    طباعة
                                </a>
                            </li>'''
    
    if old not in content:
        return False, "لم يتم العثور على السطر المطلوب"
    
    content = content.replace(old, new)
    list_path.write_text(content, encoding='utf-8')
    
    return True, "تم تحديث list.html"


def add_print_button_to_detail():
    """إضافة زرار طباعة في صفحة تفاصيل الموظف"""
    detail_path = BASE_DIR / 'templates' / 'employees' / 'detail.html'
    
    if not detail_path.exists():
        return False, "ملف detail.html مش موجود"
    
    content = detail_path.read_text(encoding='utf-8')
    
    if 'print_detail' in content:
        return True, "زرار الطباعة موجود بالفعل"
    
    old = '''<a href="{% url 'employees:edit' employee.pk %}" class="btn btn-primary">
                        <i class="bi bi-pencil-square"></i>
                        تعديل البيانات
                    </a>
                    <a href="{% url 'employees:delete' employee.pk %}" class="btn btn-outline-danger">
                        <i class="bi bi-trash"></i>
                        حذف الموظف
                    </a>'''
    
    new = '''<a href="{% url 'employees:edit' employee.pk %}" class="btn btn-primary">
                        <i class="bi bi-pencil-square"></i>
                        تعديل البيانات
                    </a>
                    <a href="{% url 'employees:print_detail' employee.pk %}" class="btn btn-outline-info" target="_blank">
                        <i class="bi bi-printer"></i>
                        طباعة البيانات
                    </a>
                    <a href="{% url 'employees:delete' employee.pk %}" class="btn btn-outline-danger">
                        <i class="bi bi-trash"></i>
                        حذف الموظف
                    </a>'''
    
    if old not in content:
        return False, "لم يتم العثور على أزرار الإجراءات"
    
    content = content.replace(old, new)
    detail_path.write_text(content, encoding='utf-8')
    
    return True, "تم إضافة زرار الطباعة في detail.html"


def install_weasyprint():
    """تثبيت WeasyPrint"""
    print("  📦 جاري تثبيت WeasyPrint...")
    result = os.system("pip install weasyprint")
    if result == 0:
        return True, "تم تثبيت WeasyPrint"
    else:
        return False, "فشل تثبيت WeasyPrint - جرب يدوياً: pip install weasyprint"


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def create_file(relative_path, content):
    full_path = BASE_DIR / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')
    return True


def main():
    print("=" * 60)
    print("🚀 Patch 02: Employees - PDF + Print + Edit")
    print("=" * 60)
    print()
    
    # إنشاء الملفات
    print("📁 إنشاء ملفات الطباعة...")
    print("-" * 60)
    
    for file_path, content in FILES.items():
        try:
            create_file(file_path, content)
            print(f"  ✅ {file_path}")
        except Exception as e:
            print(f"  ❌ {file_path}: {e}")
    
    print()
    print("🔧 تحديث الملفات الموجودة...")
    print("-" * 60)
    
    updates = [
        ('employees/views.py', update_employee_views),
        ('employees/urls.py', update_employee_urls),
        ('templates/employees/list.html', update_employee_list_template),
        ('templates/employees/detail.html', add_print_button_to_detail),
    ]
    
    for name, func in updates:
        try:
            success, message = func()
            icon = "✅" if success else "⚠️"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print()
    print("📦 تثبيت المكتبات المطلوبة...")
    print("-" * 60)
    
    success, message = install_weasyprint()
    icon = "✅" if success else "⚠️"
    print(f"  {icon} {message}")
    
    print()
    print("=" * 60)
    print("✨ تم الانتهاء!")
    print("=" * 60)
    print()
    print("الخطوات التالية:")
    print("  1. شغل السيرفر: python manage.py runserver 0.0.0.0:8000")
    print("  2. روح لصفحة الموظفين")
    print("  3. اضغط 'تصدير' → 'PDF' لتحميل PDF")
    print("  4. اضغط 'تصدير' → 'طباعة' لصفحة طباعة")
    print("  5. من تفاصيل موظف اضغط 'طباعة البيانات'")
    print()
    print("⚠️  ملاحظة: لو ظهر خطأ في WeasyPrint على Windows:")
    print("     تحتاج تثبت GTK3: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer")
    print()


if __name__ == '__main__':
    main()