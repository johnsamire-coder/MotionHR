#!/usr/bin/env python3
"""
Patch 42c: Schedule Management UI
===================================
1) صفحة الجدولة الأسبوعية
2) إضافة / تعديل تكليف يومي
3) عرض الأسبوع لكل الموظفين
4) Sidebar link
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


print("=" * 60)
print("  Patch 42c: Schedule Management UI")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) Views
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

schedule_views = '''

# ════════════════════════════════════════════════════════════
# Schedule Management
# ════════════════════════════════════════════════════════════

@login_required
def schedule_week_view(request):
    """عرض جدول الأسبوع لكل الموظفين"""
    from attendance.models import DailyAssignment
    from employees.models import Employee
    from datetime import timedelta
    from django.utils import timezone

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    company = request.user.company
    today = timezone.now().date()

    # نقطة بداية الأسبوع
    week_offset = int(request.GET.get("week", 0))
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)

    # بناء أيام الأسبوع
    days = []
    day_names = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    for i in range(7):
        d = week_start + timedelta(days=i)
        days.append({
            "date": d,
            "name": day_names[i],
            "is_today": d == today,
        })

    # الموظفين
    if role == "manager":
        current_emp = Employee.all_objects.filter(user=request.user).first()
        if current_emp:
            employees = Employee.all_objects.filter(
                company=company,
                direct_manager=current_emp,
                status="active"
            ).select_related("department", "job_title")
        else:
            employees = Employee.all_objects.none()
    else:
        employees = Employee.all_objects.filter(
            company=company,
            status="active"
        ).select_related("department", "job_title")

    # التكليفات
    assignments = DailyAssignment.objects.filter(
        company=company,
        date__range=[week_start, week_start + timedelta(days=6)]
    ).select_related("employee")

    # بناء matrix
    assignment_map = {}
    for a in assignments:
        key = f"{a.employee_id}_{a.date}"
        assignment_map[key] = a

    schedule_rows = []
    for emp in employees:
        row = {
            "employee": emp,
            "days": [],
        }
        for day_info in days:
            key = f"{emp.id}_{day_info['date']}"
            assignment = assignment_map.get(key)
            row["days"].append({
                "date": day_info["date"],
                "assignment": assignment,
            })
        schedule_rows.append(row)

    context = {
        "days": days,
        "schedule_rows": schedule_rows,
        "week_start": week_start,
        "week_end": week_start + timedelta(days=6),
        "week_offset": week_offset,
        "prev_week": week_offset - 1,
        "next_week": week_offset + 1,
        "page_title": "جدول العمل الأسبوعي",
    }
    return render(request, "attendance/schedule_week.html", context)


@login_required
def assignment_add(request):
    """إضافة تكليف يومي"""
    from attendance.models import DailyAssignment, Shift
    from employees.models import Employee

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية")
        return redirect("dashboard")

    company = request.user.company
    employees = Employee.all_objects.filter(company=company, status="active")
    shifts = Shift.objects.filter(company=company)

    if request.method == "POST":
        emp_id = request.POST.get("employee")
        date_str = request.POST.get("date")
        day_type = request.POST.get("day_type", "work_day")
        work_mode = request.POST.get("work_mode", "fixed")

        if not emp_id or not date_str:
            messages.error(request, "الموظف والتاريخ مطلوبين")
        else:
            from datetime import date as dt_date
            emp = get_object_or_404(Employee.all_objects, pk=emp_id, company=company)
            d = dt_date.fromisoformat(date_str)

            existing = DailyAssignment.objects.filter(
                company=company, employee=emp, date=d
            ).first()

            if existing:
                obj = existing
            else:
                obj = DailyAssignment(company=company, employee=emp, date=d)

            obj.day_type = day_type
            obj.work_mode = work_mode
            obj.start_time = request.POST.get("start_time") or None
            obj.end_time = request.POST.get("end_time") or None
            obj.expected_hours = request.POST.get("expected_hours") or None
            obj.segment_2_start = request.POST.get("segment_2_start") or None
            obj.segment_2_end = request.POST.get("segment_2_end") or None
            obj.is_replacement = "is_replacement" in request.POST
            obj.is_extra_shift = "is_extra_shift" in request.POST
            obj.count_as_overtime = "count_as_overtime" in request.POST
            obj.requires_tracking = "requires_tracking" in request.POST
            obj.requires_visits = "requires_visits" in request.POST
            obj.requires_geofence = "requires_geofence" in request.POST
            obj.task_title = request.POST.get("task_title", "")
            obj.location_name = request.POST.get("location_name", "")
            obj.notes = request.POST.get("notes", "")
            obj.approved_by = request.user

            shift_id = request.POST.get("shift")
            if shift_id:
                obj.shift = get_object_or_404(Shift, pk=shift_id, company=company)

            replaces_id = request.POST.get("replaces_employee")
            if replaces_id:
                obj.replaces_employee = get_object_or_404(
                    Employee.all_objects, pk=replaces_id, company=company
                )

            obj.save()

            action = "تحديث" if existing else "إضافة"
            messages.success(request, f"تم {action} التكليف بنجاح")
            return redirect("attendance:schedule_week")

    # Pre-fill من URL params
    pre_employee = request.GET.get("employee", "")
    pre_date = request.GET.get("date", "")

    context = {
        "employees": employees,
        "shifts": shifts,
        "pre_employee": pre_employee,
        "pre_date": pre_date,
        "page_title": "إضافة / تعديل تكليف",
    }
    return render(request, "attendance/assignment_form.html", context)
'''

if "def schedule_week_view" not in views:
    views += schedule_views
    write_file(views_path, views)
    print("  ✅ تم إضافة Schedule views")
else:
    print("  ℹ️  Schedule views موجودة")


# ════════════════════════════════════════════════════════════
# 2) URLs
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/urls.py...")

urls_path = os.path.join(BASE_DIR, "attendance", "urls.py")
urls = read_file(urls_path)

if "schedule" not in urls:
    urls = urls.rstrip()
    if urls.endswith("]"):
        urls = urls[:-1]
        urls += """
    # Schedule
    path('schedule/', views.schedule_week_view, name='schedule_week'),
    path('schedule/assignment/', views.assignment_add, name='assignment_add'),
]
"""
        write_file(urls_path, urls)
        print("  ✅ تم إضافة URLs")
else:
    print("  ℹ️  URLs موجودة")


# ════════════════════════════════════════════════════════════
# 3) Templates
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء Templates...")

# schedule_week.html
create_file(
    os.path.join(BASE_DIR, "templates", "attendance", "schedule_week.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}جدول العمل{% endblock %}

{% block extra_css %}
<style>
  .schedule-table { font-size:0.82rem; }
  .schedule-table th { text-align:center; white-space:nowrap; }
  .schedule-cell {
    min-width:100px; text-align:center; padding:6px 4px;
    border-radius:6px; font-size:0.78rem; cursor:pointer;
    transition:all 0.2s;
  }
  .schedule-cell:hover { transform:scale(1.05); box-shadow:0 2px 8px rgba(0,0,0,0.1); }
  .cell-work { background:#e0f7fa; color:#0e7490; }
  .cell-off { background:#f3f4f6; color:#9ca3af; }
  .cell-leave { background:#fde8e8; color:#dc2626; }
  .cell-holiday { background:#fef3c7; color:#d97706; }
  .cell-field { background:#d1fae5; color:#059669; }
  .cell-extra { background:#ede9fe; color:#7c3aed; }
  .cell-mission { background:#dbeafe; color:#2563eb; }
  .cell-empty { background:#fafafa; color:#d1d5db; border:1px dashed #e5e7eb; }
  .today-col { background:#f0f9ff !important; }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-calendar3 me-2" style="color:#06B6D4;"></i>
        جدول العمل الأسبوعي
      </h4>
      <p class="text-muted mb-0">
        {{ week_start|date:"d/m/Y" }} — {{ week_end|date:"d/m/Y" }}
      </p>
    </div>
    <div class="d-flex gap-2">
      <a href="?week={{ prev_week }}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-chevron-right"></i> الأسبوع السابق
      </a>
      <a href="?week=0" class="btn btn-sm btn-outline-primary">اليوم</a>
      <a href="?week={{ next_week }}" class="btn btn-sm btn-outline-secondary">
        الأسبوع التالي <i class="bi bi-chevron-left"></i>
      </a>
      <a href="{% url 'attendance:assignment_add' %}"
         class="btn btn-sm text-white" style="background:#06B6D4;">
        <i class="bi bi-plus-lg me-1"></i>تكليف جديد
      </a>
    </div>
  </div>

  <div class="card border-0 shadow-sm">
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-bordered mb-0 schedule-table">
          <thead>
            <tr style="background:#f8fafc;">
              <th class="px-3 py-3 text-end" style="min-width:160px;">الموظف</th>
              {% for day in days %}
              <th class="py-3 {% if day.is_today %}today-col{% endif %}">
                <div>{{ day.name }}</div>
                <small class="text-muted">{{ day.date|date:"d/m" }}</small>
              </th>
              {% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for row in schedule_rows %}
            <tr>
              <td class="px-3 py-2 text-end">
                <div class="fw-semibold">{{ row.employee.full_name_ar }}</div>
                <small class="text-muted">{{ row.employee.employee_code }}</small>
              </td>
              {% for day_data in row.days %}
              <td class="p-1 {% if day_data.date == today %}today-col{% endif %}">
                {% if day_data.assignment %}
                  {% with a=day_data.assignment %}
                  <a href="{% url 'attendance:assignment_add' %}?employee={{ row.employee.pk }}&date={{ day_data.date|date:'Y-m-d' }}"
                     class="d-block schedule-cell
                       {% if a.day_type == 'off_day' %}cell-off
                       {% elif a.day_type == 'leave_day' %}cell-leave
                       {% elif a.day_type == 'holiday' %}cell-holiday
                       {% elif a.day_type == 'mission_day' %}cell-mission
                       {% elif a.is_extra_shift %}cell-extra
                       {% elif a.work_mode == 'field' %}cell-field
                       {% else %}cell-work{% endif %}"
                     title="{{ a.get_day_type_display }} - {{ a.get_work_mode_display }}">
                    {% if a.day_type == 'off_day' %}راحة
                    {% elif a.day_type == 'leave_day' %}إجازة
                    {% elif a.day_type == 'holiday' %}رسمية
                    {% elif a.day_type == 'mission_day' %}مهمة
                    {% elif a.is_extra_shift %}إضافي
                    {% elif a.work_mode == 'field' %}ميداني
                    {% elif a.work_mode == 'flexible' %}مرن
                    {% elif a.work_mode == 'split' %}متقسم
                    {% elif a.work_mode == 'remote' %}عن بُعد
                    {% else %}عمل{% endif %}
                    {% if a.start_time %}
                    <br><small>{{ a.start_time|time:"H:i" }}</small>
                    {% endif %}
                  </a>
                  {% endwith %}
                {% else %}
                  <a href="{% url 'attendance:assignment_add' %}?employee={{ row.employee.pk }}&date={{ day_data.date|date:'Y-m-d' }}"
                     class="d-block schedule-cell cell-empty"
                     title="إضافة تكليف">
                    +
                  </a>
                {% endif %}
              </td>
              {% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Legend -->
  <div class="card border-0 shadow-sm mt-3">
    <div class="card-body p-3">
      <div class="d-flex flex-wrap gap-3">
        <span class="d-flex align-items-center gap-1">
          <span class="schedule-cell cell-work px-2">عمل</span>
        </span>
        <span class="d-flex align-items-center gap-1">
          <span class="schedule-cell cell-off px-2">راحة</span>
        </span>
        <span class="d-flex align-items-center gap-1">
          <span class="schedule-cell cell-leave px-2">إجازة</span>
        </span>
        <span class="d-flex align-items-center gap-1">
          <span class="schedule-cell cell-holiday px-2">رسمية</span>
        </span>
        <span class="d-flex align-items-center gap-1">
          <span class="schedule-cell cell-field px-2">ميداني</span>
        </span>
        <span class="d-flex align-items-center gap-1">
          <span class="schedule-cell cell-extra px-2">إضافي</span>
        </span>
        <span class="d-flex align-items-center gap-1">
          <span class="schedule-cell cell-mission px-2">مهمة</span>
        </span>
        <span class="d-flex align-items-center gap-1">
          <span class="schedule-cell cell-empty px-2">+</span> فارغ
        </span>
      </div>
    </div>
  </div>

</div>
{% endblock %}
"""
)

# assignment_form.html
create_file(
    os.path.join(BASE_DIR, "templates", "attendance", "assignment_form.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'attendance:schedule_week' %}" class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">{{ page_title }}</h4>
  </div>

  <div class="row justify-content-center">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الموظف <span class="text-danger">*</span></label>
                <select name="employee" class="form-select" required>
                  <option value="">اختر الموظف</option>
                  {% for emp in employees %}
                  <option value="{{ emp.pk }}"
                    {% if pre_employee == emp.pk|stringformat:"d" %}selected{% endif %}>
                    {{ emp.full_name_ar }} ({{ emp.employee_code }})
                  </option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">التاريخ <span class="text-danger">*</span></label>
                <input type="date" name="date" class="form-control" required
                       value="{{ pre_date }}">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">نوع اليوم</label>
                <select name="day_type" class="form-select">
                  <option value="work_day">يوم عمل</option>
                  <option value="off_day">راحة أسبوعية</option>
                  <option value="leave_day">إجازة</option>
                  <option value="holiday">إجازة رسمية</option>
                  <option value="mission_day">مأمورية / مهمة</option>
                  <option value="standby_day">استدعاء</option>
                  <option value="training_day">يوم تدريب</option>
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">طريقة التنفيذ</label>
                <select name="work_mode" class="form-select">
                  <option value="fixed">ثابت</option>
                  <option value="flexible">مرن</option>
                  <option value="split">متقسم</option>
                  <option value="field">ميداني</option>
                  <option value="remote">عن بُعد</option>
                  <option value="mixed">مختلط</option>
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الشيفت</label>
                <select name="shift" class="form-select">
                  <option value="">بدون</option>
                  {% for s in shifts %}
                  <option value="{{ s.pk }}">{{ s.name }}</option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الساعات المتوقعة</label>
                <input type="number" name="expected_hours" class="form-control"
                       step="0.5" min="0" value="8">
              </div>

              <div class="col-md-3">
                <label class="form-label fw-semibold small">بداية العمل</label>
                <input type="time" name="start_time" class="form-control">
              </div>

              <div class="col-md-3">
                <label class="form-label fw-semibold small">نهاية العمل</label>
                <input type="time" name="end_time" class="form-control">
              </div>

              <div class="col-md-3">
                <label class="form-label fw-semibold small">جزء 2 بداية</label>
                <input type="time" name="segment_2_start" class="form-control">
              </div>

              <div class="col-md-3">
                <label class="form-label fw-semibold small">جزء 2 نهاية</label>
                <input type="time" name="segment_2_end" class="form-control">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">عنوان المهمة</label>
                <input type="text" name="task_title" class="form-control"
                       placeholder="لو مهمة محددة">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الموقع</label>
                <input type="text" name="location_name" class="form-control"
                       placeholder="اسم الموقع">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">بديل عن موظف</label>
                <select name="replaces_employee" class="form-select">
                  <option value="">لا أحد</option>
                  {% for emp in employees %}
                  <option value="{{ emp.pk }}">{{ emp.full_name_ar }}</option>
                  {% endfor %}
                </select>
              </div>

              <!-- Flags -->
              <div class="col-12">
                <div class="d-flex flex-wrap gap-3">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="is_replacement" id="isReplacement">
                    <label class="form-check-label small" for="isReplacement">بديل لزميل</label>
                  </div>
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="is_extra_shift" id="isExtra">
                    <label class="form-check-label small" for="isExtra">شيفت إضافي</label>
                  </div>
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="count_as_overtime" id="asOvertime">
                    <label class="form-check-label small" for="asOvertime">يحسب أوفر تايم</label>
                  </div>
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="requires_tracking" id="needsTracking">
                    <label class="form-check-label small" for="needsTracking">يحتاج تتبع GPS</label>
                  </div>
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="requires_visits" id="needsVisits">
                    <label class="form-check-label small" for="needsVisits">يحتاج زيارات</label>
                  </div>
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="requires_geofence" id="needsGeo" checked>
                    <label class="form-check-label small" for="needsGeo">يحتاج نطاق الفرع</label>
                  </div>
                </div>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">ملاحظات</label>
                <textarea name="notes" class="form-control" rows="2"></textarea>
              </div>

            </div>

            <div class="d-flex gap-2 mt-4 pt-3 border-top">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>حفظ التكليف
              </button>
              <a href="{% url 'attendance:schedule_week' %}"
                 class="btn btn-outline-secondary px-4" style="border-radius:10px;">
                إلغاء
              </a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""
)

# ════════════════════════════════════════════════════════════
# 4) Sidebar link
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "attendance:schedule_week" not in sidebar:
    target = """      <a href="{% url 'attendance:late_notifications' %}"
         class="nav-link {% if 'late-notifications' in request.path %}active{% endif %}">
        <i class="bi bi-bell"></i><span>إشعارات التأخير</span>
      </a>"""

    replacement = target + """
      <a href="{% url 'attendance:schedule_week' %}"
         class="nav-link {% if 'schedule' in request.path %}active{% endif %}">
        <i class="bi bi-calendar3"></i><span>جدول العمل</span>
      </a>"""

    if target in sidebar:
        sidebar = sidebar.replace(target, replacement)
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة رابط جدول العمل")
    else:
        print("  ℹ️  مكان مختلف")
else:
    print("  ℹ️  رابط جدول العمل موجود")


print("\n" + "=" * 60)
print("  ✅ Patch 42c اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ schedule_week_view — جدول أسبوعي لكل الموظفين
  2. ✅ assignment_add — إضافة / تعديل تكليف يومي
  3. ✅ schedule_week.html — جدول ملون بالأنواع
  4. ✅ assignment_form.html — فورم كامل
  5. ✅ URLs
  6. ✅ Sidebar link

جرب:
  demo_admin / hr_manager
  /attendance/schedule/
  - جدول ملون
  - اضغط على خانة لتعديل أو إضافة تكليف
""")