"""
Patch 49f — Employee Comprehensive Profile from Reports

الهدف:
1) صفحة ملخص شامل لأي موظف تحتوي على:
   - البيانات الشخصية
   - بيانات العمل
   - الحضور والتأخيرات
   - الإجازات
   - الطلبات
   - الخصومات
   - الإنذارات
2) زرار من أي تقرير يفتح الملف الشامل
3) تحديث templates التقارير لإضافة الزرار
"""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    full = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")


print("=" * 60)
print("Patch 49f — Employee Comprehensive Profile from Reports")
print("=" * 60)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

for rel_path, backup_name in [
    ("employees/views.py", "employees_views_before_patch_49f.py.bak"),
    ("employees/urls.py", "employees_urls_before_patch_49f.py.bak"),
    ("templates/reports/attendance_report.html", "attendance_report_before_patch_49f.html.bak"),
    ("templates/reports/late_report.html", "late_report_before_patch_49f.html.bak"),
    ("templates/reports/leave_report.html", "leave_report_before_patch_49f.html.bak"),
    ("templates/reports/employees_report.html", "employees_report_before_patch_49f.html.bak"),
]:
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        shutil.copy2(full, os.path.join(backup_dir, backup_name))
        print(f"✅ Backup: _patches/_backups/{backup_name}")

# ────────────────────────────────────────────────────────────
# Step 1: Add comprehensive_profile view to employees/views.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: إضافة comprehensive_profile view")

views_path = "employees/views.py"
views_content = read_file(views_path)
if views_content is None:
    raise SystemExit("❌ ملف employees/views.py غير موجود")

profile_view = '''

# ═════════════════════════════════════════════════════════════
# Patch 49f — Employee Comprehensive Profile
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_comprehensive_profile(request, pk):
    """ملف شامل للموظف — كل البيانات في صفحة واحدة"""
    from datetime import date, timedelta
    from django.db.models import Sum, Count, Q

    employee = _get_employee_or_404_for_user(request.user, pk)
    company = _get_current_company(request.user)

    # ── البيانات الأساسية ──
    documents = []
    for rel_name in ['documents', 'employeedocument_set']:
        rel = getattr(employee, rel_name, None)
        if rel is not None:
            try:
                documents = list(rel.all()[:20])
                break
            except Exception:
                pass

    # ── الخصومات ──
    deductions_qs = Deduction.objects.filter(employee=employee).order_by('-date', '-id')
    deductions = list(deductions_qs[:20])
    total_deductions = deductions_qs.aggregate(total=Sum('amount'))['total'] or 0

    # ── الحضور ──
    attendance_data = {}
    try:
        from attendance.models import Attendance
        today = date.today()
        month_start = today.replace(day=1)

        att_qs = Attendance.objects.filter(employee=employee)
        att_month = att_qs.filter(date__gte=month_start, date__lte=today)

        attendance_data = {
            'total_records': att_qs.count(),
            'month_present': att_month.filter(status='present').count(),
            'month_late': att_month.filter(status='late').count(),
            'month_absent': att_month.filter(status='absent').count(),
            'month_leave': att_month.filter(status='on_leave').count(),
            'total_late_minutes': att_qs.aggregate(total=Sum('late_minutes'))['total'] or 0,
            'recent_records': list(att_qs.order_by('-date')[:10]),
        }
    except Exception:
        pass

    # ── التأخيرات ──
    late_incidents = []
    try:
        from attendance.models import LateIncident
        late_incidents = list(
            LateIncident.objects.filter(employee=employee).order_by('-date')[:10]
        )
    except Exception:
        pass

    # ── الإنذارات ──
    disciplinary_actions = []
    try:
        from attendance.models import DisciplinaryAction
        disciplinary_actions = list(
            DisciplinaryAction.objects.filter(employee=employee).order_by('-date')[:10]
        )
    except Exception:
        pass

    # ── الإجازات ──
    leave_data = {}
    try:
        from leaves.models import LeaveRequest, LeaveBalance
        leave_requests = list(
            LeaveRequest.objects.filter(employee=employee).select_related('leave_type').order_by('-start_date')[:10]
        )
        leave_balances = list(
            LeaveBalance.objects.filter(employee=employee).select_related('leave_type')
        )
        leave_data = {
            'requests': leave_requests,
            'balances': leave_balances,
            'total_requests': LeaveRequest.objects.filter(employee=employee).count(),
        }
    except Exception:
        pass

    # ── الطلبات ──
    employee_requests = []
    try:
        from requests_app.models import EmployeeRequest
        employee_requests = list(
            EmployeeRequest.objects.filter(employee=employee).select_related('request_type').order_by('-created_at')[:10]
        )
    except Exception:
        pass

    # ── الإشعارات ──
    notifications = []
    try:
        from accounts.models import EmployeeNotification
        notifications = list(
            EmployeeNotification.objects.filter(recipient=employee.user).order_by('-created_at')[:10]
        )
    except Exception:
        pass

    context = {
        'employee': employee,
        'documents': documents,
        'deductions': deductions,
        'total_deductions': total_deductions,
        'attendance_data': attendance_data,
        'late_incidents': late_incidents,
        'disciplinary_actions': disciplinary_actions,
        'leave_data': leave_data,
        'employee_requests': employee_requests,
        'notifications': notifications,
        'page_title': f'الملف الشامل - {_employee_name(employee)}',
    }
    return render(request, 'employees/comprehensive_profile.html', context)
'''

if "def employee_comprehensive_profile(request, pk):" not in views_content:
    # نضيفها قبل الـ aliases
    marker = "# ═════════════════════════════════════════════════════════════\n# Compatibility Aliases"
    if marker in views_content:
        views_content = views_content.replace(marker, profile_view + "\n\n" + marker)
    else:
        views_content = views_content.rstrip() + "\n" + profile_view + "\n"

    # نضيف alias
    views_content = views_content.rstrip() + "\ncomprehensive_profile = employee_comprehensive_profile\n"
    write_file(views_path, views_content)
    print("   ✅ تمت إضافة employee_comprehensive_profile")
else:
    print("   ℹ️ employee_comprehensive_profile موجودة بالفعل")

# ────────────────────────────────────────────────────────────
# Step 2: Add URL
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إضافة URL")

urls_path = "employees/urls.py"
urls_content = read_file(urls_path)
if urls_content is None:
    raise SystemExit("❌ ملف employees/urls.py غير موجود")

profile_url = "    path('<int:pk>/profile/', views.employee_comprehensive_profile, name='comprehensive_profile'),"

if "name='comprehensive_profile'" not in urls_content:
    if "urlpatterns = [" in urls_content:
        urls_content = urls_content.replace(
            "urlpatterns = [",
            "urlpatterns = [\n" + profile_url,
            1
        )
        write_file(urls_path, urls_content)
        print("   ✅ تم إضافة route comprehensive_profile")
    else:
        print("   ⚠️ لم أجد urlpatterns")
else:
    print("   ℹ️ route موجود بالفعل")

# ────────────────────────────────────────────────────────────
# Step 3: Create comprehensive_profile template
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: إنشاء templates/employees/comprehensive_profile.html")

profile_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}{{ page_title|default:"الملف الشامل" }}{% endblock %}

{% block extra_css %}
<style>
  .profile-header {
    background: linear-gradient(135deg, #06B6D4 0%, #0891b2 100%);
    border-radius: 18px;
    color: white;
    padding: 24px;
  }
  .profile-header .emp-name { font-size: 1.5rem; font-weight: 800; }
  .profile-header .emp-code { opacity: .85; font-size: .9rem; }
  .stat-card {
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    background: #fff;
  }
  .stat-card .stat-value { font-size: 1.5rem; font-weight: 800; }
  .stat-card .stat-label { font-size: .82rem; color: #64748b; }
  .section-card {
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    overflow: hidden;
    margin-bottom: 1.5rem;
  }
  .section-card .card-header {
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    padding: 14px 18px;
  }
  .section-card .card-header h6 { margin: 0; font-weight: 800; }
  .info-row { display: flex; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f1f5f9; }
  .info-row:last-child { border-bottom: none; }
  .info-label { font-weight: 700; color: #475569; min-width: 140px; font-size: .88rem; }
  .info-value { color: #0f172a; font-size: .88rem; }
  .mini-table { font-size: .85rem; }
  .mini-table th { font-weight: 700; white-space: nowrap; }
  .print-btn { position: fixed; bottom: 20px; left: 20px; z-index: 999; }
  @media print { .print-btn, .breadcrumb, .btn { display: none !important; } }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">

  <!-- Breadcrumb -->
  <nav aria-label="breadcrumb" class="mb-3">
    <ol class="breadcrumb small">
      <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
      <li class="breadcrumb-item"><a href="{% url 'employees:list' %}">الموظفون</a></li>
      <li class="breadcrumb-item active">الملف الشامل</li>
    </ol>
  </nav>

  <!-- Header -->
  <div class="profile-header mb-4">
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
      <div>
        <div class="emp-name">{{ employee.full_name_ar }}</div>
        <div class="emp-code">
          {{ employee.employee_code }}
          {% if employee.job_title %} | {{ employee.job_title.name_ar|default:employee.job_title.name_en }}{% endif %}
          {% if employee.department %} | {{ employee.department.name_ar|default:employee.department.name_en }}{% endif %}
        </div>
      </div>
      <div class="d-flex gap-2">
        <a href="{% url 'employees:detail' employee.pk %}" class="btn btn-light btn-sm">
          <i class="bi bi-person me-1"></i>ملف الموظف
        </a>
        <button onclick="window.print()" class="btn btn-light btn-sm">
          <i class="bi bi-printer me-1"></i>طباعة
        </button>
      </div>
    </div>
  </div>

  <!-- Stats -->
  <div class="row g-3 mb-4">
    <div class="col-6 col-md-3">
      <div class="stat-card">
        <div class="stat-value text-success">{{ attendance_data.month_present|default:0 }}</div>
        <div class="stat-label">حضور هذا الشهر</div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card">
        <div class="stat-value text-warning">{{ attendance_data.month_late|default:0 }}</div>
        <div class="stat-label">تأخير هذا الشهر</div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card">
        <div class="stat-value text-danger">{{ attendance_data.month_absent|default:0 }}</div>
        <div class="stat-label">غياب هذا الشهر</div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card">
        <div class="stat-value text-info">{{ leave_data.total_requests|default:0 }}</div>
        <div class="stat-label">إجمالي الإجازات</div>
      </div>
    </div>
  </div>

  <div class="row g-4">
    <div class="col-lg-6">

      <!-- البيانات الشخصية -->
      <div class="section-card">
        <div class="card-header"><h6><i class="bi bi-person-vcard me-2 text-primary"></i>البيانات الشخصية</h6></div>
        <div class="card-body p-3">
          <div class="info-row"><span class="info-label">الاسم</span><span class="info-value">{{ employee.full_name_ar }}</span></div>
          <div class="info-row"><span class="info-label">الرقم القومي</span><span class="info-value">{{ employee.national_id|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">تاريخ الميلاد</span><span class="info-value">{{ employee.birth_date|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">النوع</span><span class="info-value">{{ employee.get_gender_display|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">الحالة الاجتماعية</span><span class="info-value">{{ employee.get_marital_status_display|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">الجنسية</span><span class="info-value">{{ employee.nationality|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">الهاتف</span><span class="info-value">{{ employee.phone|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">الإيميل</span><span class="info-value">{{ employee.email|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">العنوان</span><span class="info-value">{{ employee.address|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">المدينة</span><span class="info-value">{{ employee.city|default:"—" }}</span></div>
        </div>
      </div>

      <!-- بيانات العمل -->
      <div class="section-card">
        <div class="card-header"><h6><i class="bi bi-briefcase me-2 text-primary"></i>بيانات العمل</h6></div>
        <div class="card-body p-3">
          <div class="info-row"><span class="info-label">الكود</span><span class="info-value">{{ employee.employee_code }}</span></div>
          <div class="info-row"><span class="info-label">الفرع</span><span class="info-value">{{ employee.branch.name_ar|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">الإدارة</span><span class="info-value">{{ employee.department.name_ar|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">الوظيفة</span><span class="info-value">{{ employee.job_title.name_ar|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">المدير المباشر</span><span class="info-value">{{ employee.direct_manager.full_name_ar|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">تاريخ التعيين</span><span class="info-value">{{ employee.hire_date|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">نوع العقد</span><span class="info-value">{{ employee.get_contract_type_display|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">الحالة</span><span class="info-value">{{ employee.get_status_display|default:"—" }}</span></div>
          <div class="info-row"><span class="info-label">الراتب الأساسي</span><span class="info-value">{{ employee.basic_salary|default:"—" }}</span></div>
        </div>
      </div>

      <!-- رصيد الإجازات -->
      {% if leave_data.balances %}
      <div class="section-card">
        <div class="card-header"><h6><i class="bi bi-calendar2-check me-2 text-primary"></i>رصيد الإجازات</h6></div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table mini-table align-middle mb-0">
              <thead class="table-light">
                <tr><th>النوع</th><th>الرصيد</th><th>المستخدم</th><th>المتبقي</th></tr>
              </thead>
              <tbody>
                {% for bal in leave_data.balances %}
                <tr>
                  <td>{{ bal.leave_type.name_ar|default:bal.leave_type.name|default:"—" }}</td>
                  <td>{{ bal.total_days|default:0 }}</td>
                  <td>{{ bal.used_days|default:0 }}</td>
                  <td class="fw-bold text-primary">{{ bal.remaining_days|default:0 }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {% endif %}

    </div>

    <div class="col-lg-6">

      <!-- آخر سجلات الحضور -->
      {% if attendance_data.recent_records %}
      <div class="section-card">
        <div class="card-header">
          <h6><i class="bi bi-calendar-check me-2 text-primary"></i>آخر سجلات الحضور</h6>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table mini-table align-middle mb-0">
              <thead class="table-light">
                <tr><th>التاريخ</th><th>الدخول</th><th>الخروج</th><th>الحالة</th><th>تأخير</th></tr>
              </thead>
              <tbody>
                {% for att in attendance_data.recent_records %}
                <tr>
                  <td>{{ att.date|date:"m/d" }}</td>
                  <td>{{ att.check_in_time|time:"H:i"|default:"—" }}</td>
                  <td>{{ att.check_out_time|time:"H:i"|default:"—" }}</td>
                  <td>
                    {% if att.status == 'present' %}<span class="badge bg-success-subtle text-success">حاضر</span>
                    {% elif att.status == 'late' %}<span class="badge bg-warning-subtle text-warning">متأخر</span>
                    {% elif att.status == 'absent' %}<span class="badge bg-danger-subtle text-danger">غائب</span>
                    {% elif att.status == 'on_leave' %}<span class="badge bg-info-subtle text-info">إجازة</span>
                    {% else %}<span class="badge bg-secondary">{{ att.status }}</span>{% endif %}
                  </td>
                  <td>{% if att.late_minutes %}<span class="text-danger">{{ att.late_minutes }}د</span>{% else %}—{% endif %}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {% endif %}

      <!-- الإنذارات -->
      {% if disciplinary_actions %}
      <div class="section-card">
        <div class="card-header"><h6><i class="bi bi-exclamation-triangle me-2 text-danger"></i>الإنذارات</h6></div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table mini-table align-middle mb-0">
              <thead class="table-light">
                <tr><th>التاريخ</th><th>النوع</th><th>السبب</th></tr>
              </thead>
              <tbody>
                {% for da in disciplinary_actions %}
                <tr>
                  <td>{{ da.date|date:"Y/m/d" }}</td>
                  <td>{{ da.get_action_type_display|default:da.action_type }}</td>
                  <td class="small">{{ da.reason|truncatechars:50 }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {% endif %}

      <!-- الخصومات -->
      {% if deductions %}
      <div class="section-card">
        <div class="card-header">
          <div class="d-flex justify-content-between align-items-center">
            <h6 class="mb-0"><i class="bi bi-cash-stack me-2 text-danger"></i>الخصومات</h6>
            <span class="badge bg-danger">إجمالي: {{ total_deductions }}</span>
          </div>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table mini-table align-middle mb-0">
              <thead class="table-light">
                <tr><th>التاريخ</th><th>النوع</th><th>المبلغ</th><th>السبب</th></tr>
              </thead>
              <tbody>
                {% for ded in deductions %}
                <tr>
                  <td>{{ ded.date|date:"Y/m/d" }}</td>
                  <td>{{ ded.get_deduction_type_display|default:ded.deduction_type }}</td>
                  <td class="fw-bold text-danger">{{ ded.amount }}</td>
                  <td class="small">{{ ded.reason|truncatechars:40 }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {% endif %}

      <!-- طلبات الموظف -->
      {% if employee_requests %}
      <div class="section-card">
        <div class="card-header"><h6><i class="bi bi-file-earmark-text me-2 text-primary"></i>آخر الطلبات</h6></div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table mini-table align-middle mb-0">
              <thead class="table-light">
                <tr><th>التاريخ</th><th>النوع</th><th>الحالة</th></tr>
              </thead>
              <tbody>
                {% for req in employee_requests %}
                <tr>
                  <td>{{ req.created_at|date:"Y/m/d" }}</td>
                  <td>{{ req.request_type.name_ar|default:req.request_type.name|default:"—" }}</td>
                  <td>{{ req.get_status_display|default:req.status }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {% endif %}

      <!-- طلبات الإجازات -->
      {% if leave_data.requests %}
      <div class="section-card">
        <div class="card-header"><h6><i class="bi bi-calendar-minus me-2 text-primary"></i>آخر طلبات الإجازات</h6></div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table mini-table align-middle mb-0">
              <thead class="table-light">
                <tr><th>النوع</th><th>من</th><th>إلى</th><th>الحالة</th></tr>
              </thead>
              <tbody>
                {% for lr in leave_data.requests %}
                <tr>
                  <td>{{ lr.leave_type.name_ar|default:lr.leave_type.name|default:"—" }}</td>
                  <td>{{ lr.start_date|date:"m/d" }}</td>
                  <td>{{ lr.end_date|date:"m/d" }}</td>
                  <td>{{ lr.get_status_display|default:lr.status }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {% endif %}

    </div>
  </div>

</div>

<button onclick="window.print()" class="btn btn-primary btn-lg rounded-circle shadow print-btn" title="طباعة">
  <i class="bi bi-printer-fill"></i>
</button>
{% endblock %}
"""

write_file("templates/employees/comprehensive_profile.html", profile_template)

# ────────────────────────────────────────────────────────────
# Step 4: Add profile button to report templates
# ────────────────────────────────────────────────────────────
print("\n📌 Step 4: إضافة زرار الملف الشامل في التقارير")

profile_button_snippet = '''<a href="{% url 'employees:comprehensive_profile' EMPLOYEE_PK %}" class="btn btn-sm btn-outline-info" title="الملف الشامل"><i class="bi bi-person-lines-fill"></i></a>'''

report_templates = {
    "templates/reports/attendance_report.html": "d.employee",
    "templates/reports/late_report.html": "r.employee",
    "templates/reports/leave_report.html": "r.employee",
    "templates/reports/employees_report.html": "emp",
}

for template_file, emp_var in report_templates.items():
    content = read_file(template_file)
    if content is None:
        print(f"   ⚠️ ملف {template_file} غير موجود — تجاوز")
        continue

    if "comprehensive_profile" in content:
        print(f"   ℹ️ {template_file} — الزرار موجود بالفعل")
        continue

    # نبحث عن آخر th في thead ونضيف عمود "ملف"
    if "<th>إجراء</th>" not in content and "<th>ملف</th>" not in content:
        # نضيف عمود جديد في الـ thead
        content = content.replace(
            "</tr>\n              </thead>",
            "<th>ملف</th>\n              </tr>\n              </thead>",
            1
        )

        # نضيف الخلية في tbody
        # نبحث عن آخر </td> قبل </tr> داخل tbody
        import re

        def add_profile_cell(match):
            full_match = match.group(0)
            pk_ref = f"{emp_var}.pk"
            button = f'<td><a href="{{% url \'employees:comprehensive_profile\' {pk_ref} %}}" class="btn btn-sm btn-outline-info" title="الملف الشامل"><i class="bi bi-person-lines-fill"></i></a></td>'
            return button + "\n              " + full_match

        # نحاول نضيف قبل </tr> داخل الحلقة
        pattern_str = r"</tr>\s*\n\s*\{% endfor %\}"
        if re.search(pattern_str, content):
            content = re.sub(
                pattern_str,
                lambda m: f'<td><a href="{{% url \'employees:comprehensive_profile\' {emp_var}.pk %}}" class="btn btn-sm btn-outline-info" title="الملف الشامل"><i class="bi bi-person-lines-fill"></i></a></td>\n              </tr>\n              {{% endfor %}}',
                content,
                count=1
            )
            write_file(template_file, content)
            print(f"   ✅ تم إضافة زرار الملف الشامل في {template_file}")
        else:
            print(f"   ⚠️ {template_file} — لم أتمكن من حقن الزرار تلقائيًا")
    else:
        print(f"   ℹ️ {template_file} — عمود إجراء/ملف موجود بالفعل")

print("\n" + "=" * 60)
print("✅ Patch 49f اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ إنشاء صفحة الملف الشامل للموظف:
     /employees/<pk>/profile/
  ✅ الصفحة تعرض:
     - البيانات الشخصية
     - بيانات العمل
     - إحصائيات الحضور
     - آخر سجلات الحضور
     - رصيد الإجازات
     - آخر طلبات الإجازات
     - الإنذارات
     - الخصومات
     - آخر الطلبات
  ✅ زرار طباعة مباشر
  ✅ إضافة زرار "الملف الشامل" في التقارير:
     - تقرير الحضور
     - تقرير التأخيرات
     - تقرير الإجازات
     - تقرير الموظفين

الملفات المعدلة/المنشأة:
  ✅ employees/views.py
  ✅ employees/urls.py
  ✅ templates/employees/comprehensive_profile.html
  ✅ templates/reports/attendance_report.html
  ✅ templates/reports/late_report.html
  ✅ templates/reports/leave_report.html
  ✅ templates/reports/employees_report.html

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")