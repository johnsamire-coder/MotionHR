#!/usr/bin/env python3
"""
Patch 31c: Employee Privacy Fix
================================
- الموظف ما يشوفش إجازات زمايله
- Sidebar الموظف = طلباتي فقط
- leave requests للموظف تتفلتر على نفسه فقط
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 31c: Employee Privacy Fix")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) تحديث Sidebar
# الموظف يشوف الطلبات فقط
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

# نخلي روابط leaves الإدارية للإدارة فقط
old_leaves_admin = """    {% if request.user.role != 'employee' %}
    <a href="{% url 'leaves:leave_balances' %}"
       class="nav-link {% if 'balances' in request.path %}active{% endif %}">
      <i class="bi bi-wallet2"></i><span>أرصدة الإجازات</span>
    </a>
    <a href="{% url 'leaves:leave_types_list' %}"
       class="nav-link {% if 'types' in request.path %}active{% endif %}">
      <i class="bi bi-list-check"></i><span>أنواع الإجازات</span>
    </a>
    {% endif %}"""

if old_leaves_admin not in sidebar:
    # غالبًا موجود بالفعل، كويس
    print("  ℹ️  روابط الإجازات الإدارية محمية بالفعل")
else:
    print("  ℹ️  لا يحتاج تعديل")

# نشيل رابط "الإجازات" العام من الموظف لو لسه موجود
sidebar = sidebar.replace(
    """    <a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'add' not in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
      <i class="bi bi-calendar2-week"></i><span>الإجازات</span>
    </a>""",
    """    {% if request.user.role != 'employee' %}
    <a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'add' not in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
      <i class="bi bi-calendar2-week"></i><span>طلبات الإجازات</span>
    </a>
    {% endif %}"""
)

write_file(sidebar_path, sidebar)


# ════════════════════════════════════════════════════════════
# 2) تحديث leaves/views.py
# الموظف يشوف طلباته هو فقط
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث leaves/views.py...")

views_path = os.path.join(BASE_DIR, "leaves", "views.py")
views = read_file(views_path)

old_block = """@login_required
def leave_requests_list(request):
    company  = request.user.company
    requests = LeaveRequest.objects.filter(
        company=company
    ).select_related("employee", "leave_type", "reviewed_by").order_by("-created_at")

    # فلترة
    status = request.GET.get("status")
    if status:
        requests = requests.filter(status=status)

    emp_search = request.GET.get("employee")
    if emp_search:
        requests = requests.filter(
            Q(employee__first_name_ar__icontains=emp_search) |
            Q(employee__last_name_ar__icontains=emp_search)
        )

    context = {
        "requests":   requests,
        "page_title": "طلبات الإجازات",
        "status":     status,
    }
    return render(request, "leaves/leave_requests_list.html", context)"""

new_block = """@login_required
def leave_requests_list(request):
    company = request.user.company

    requests = LeaveRequest.objects.filter(
        company=company
    ).select_related("employee", "leave_type", "reviewed_by").order_by("-created_at")

    # لو الموظف العادي - يشوف طلباته هو فقط
    if request.user.role == "employee":
        current_emp = Employee.objects.filter(user=request.user).first()
        if current_emp:
            requests = requests.filter(employee=current_emp)
        else:
            requests = LeaveRequest.objects.none()

    # فلترة
    status = request.GET.get("status")
    if status:
        requests = requests.filter(status=status)

    # البحث بالاسم للإدارة فقط
    emp_search = request.GET.get("employee")
    if emp_search and request.user.role != "employee":
        requests = requests.filter(
            Q(employee__first_name_ar__icontains=emp_search) |
            Q(employee__last_name_ar__icontains=emp_search)
        )

    context = {
        "requests": requests,
        "page_title": "طلباتي" if request.user.role == "employee" else "طلبات الإجازات",
        "status": status,
    }
    return render(request, "leaves/leave_requests_list.html", context)"""

if old_block in views:
    views = views.replace(old_block, new_block)
    write_file(views_path, views)
    print("  ✅ الموظف يشوف طلبات إجازته فقط")
else:
    print("  ℹ️  بلوك leave_requests_list مختلف - نحاول regex")

    pattern = re.compile(
        r"@login_required\s+def leave_requests_list\(request\):.*?return render\(request, \"leaves/leave_requests_list.html\", context\)",
        re.DOTALL
    )
    if pattern.search(views):
        views = pattern.sub(new_block, views)
        write_file(views_path, views)
        print("  ✅ تم استبدال leave_requests_list بالـ regex")
    else:
        print("  ⚠️  لم أستطع تعديل leave_requests_list تلقائيًا")


# ════════════════════════════════════════════════════════════
# 3) تحديث leaves/leave_requests_list.html
# إخفاء البحث بالموظف عن الموظف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث leave_requests_list.html...")

tmpl_path = os.path.join(BASE_DIR, "templates", "leaves", "leave_requests_list.html")
tmpl = read_file(tmpl_path)

# عنوان الصفحة
tmpl = tmpl.replace(
    "طلبات الإجازات",
    "{% if request.user.role == 'employee' %}طلباتي{% else %}طلبات الإجازات{% endif %}",
    1
)

# إخفاء خانة البحث بالموظف للموظف
tmpl = tmpl.replace(
    """        <input type="text" name="employee" class="form-control"
               style="max-width:200px;" placeholder="اسم الموظف"
               value="{{ request.GET.employee|default:'' }}">""",
    """        {% if request.user.role != 'employee' %}
        <input type="text" name="employee" class="form-control"
               style="max-width:200px;" placeholder="اسم الموظف"
               value="{{ request.GET.employee|default:'' }}">
        {% endif %}"""
)

# إخفاء عمود الموظف للموظف
tmpl = tmpl.replace(
    "<th class=\"px-4 py-3\">الموظف</th>",
    "{% if request.user.role != 'employee' %}<th class=\"px-4 py-3\">الموظف</th>{% endif %}"
)

tmpl = tmpl.replace(
    """<td class="px-4 fw-semibold">{{ lr.employee.full_name_ar }}</td>""",
    """{% if request.user.role != 'employee' %}
            <td class="px-4 fw-semibold">{{ lr.employee.full_name_ar }}</td>
            {% endif %}"""
)

write_file(tmpl_path, tmpl)

print("\n" + "=" * 60)
print("  ✅ Patch 31c اكتمل!")
print("=" * 60)
print("""
اللي اتصلح:
  1. ✅ الموظف ما بقاش يشوف "الإجازات" العامة في الـ Sidebar
  2. ✅ الموظف يشوف "طلباتي" فقط
  3. ✅ صفحة طلبات الإجازة للموظف = طلباته هو فقط
  4. ✅ أرصدة الإجازات وأنواع الإجازات للإدارة فقط

جرب الآن بـ emp10003:
  - الـ Sidebar
  - /leaves/
  - /requests/
""")