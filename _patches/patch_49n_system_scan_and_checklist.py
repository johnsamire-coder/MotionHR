"""
Patch 49N — System Scan + QA Checklist

الهدف:
1) فحص آلي لكل الـ named URLs داخل المشروع باستخدام Django test client
2) الفحص على مستويات مختلفة:
   - anonymous
   - super_admin
   - company_admin
   - hr_manager
   - manager
   - employee
   - field_employee
3) استخراج تقرير شامل:
   - ما الذي يعمل 200
   - ما الذي يعمل Redirect
   - ما الذي يرجع 403/404/500
   - ما الذي لم يمكن reverse له
   - ما الذي تم تخطيه لأنه destructive
4) إنشاء Manual QA Checklist احترافية بصيغة Markdown

مخرجات الباتش:
- _patches/_reports/49n_scan_report.md
- _patches/_reports/49n_scan_results.csv
- _patches/_reports/49n_manual_qa_checklist.md

مهم:
- لا يغير أي شيء في قاعدة البيانات
- لا يضغط أزرار POST destructive
- آمن في التشغيل
"""

import os
import sys
import csv
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from django.apps import apps
from django.test import Client
from django.urls import get_resolver, URLPattern, URLResolver, reverse, NoReverseMatch
from django.contrib.auth import get_user_model

REPORT_DIR = os.path.join(BASE_DIR, "_patches", "_reports")
os.makedirs(REPORT_DIR, exist_ok=True)

SCAN_MD = os.path.join(REPORT_DIR, "49n_scan_report.md")
SCAN_CSV = os.path.join(REPORT_DIR, "49n_scan_results.csv")
CHECKLIST_MD = os.path.join(REPORT_DIR, "49n_manual_qa_checklist.md")

ALLOWED_APP_NAMESPACES = {
    "landing",
    "accounts",
    "employees",
    "attendance",
    "companies",
    "leaves",
    "requests_app",
    "reports",
    "subscriptions",
}

# Routes لا نعمل لها GET تلقائي لأنها ممكن تنفذ أكشن أو تبقى حساسة
DESTRUCTIVE_KEYWORDS = [
    "delete",
    "remove",
    "deactivate",
    "reset-password",
    "reset_password",
    "create-account",
    "create_account",
    "logout",
    "folder_delete",
]

# مسارات ماينفعش نفترضها بدون IDs
SPECIAL_STRING_KWARGS = {
    "feature_code": "payroll",
}

def safe_rel(path):
    return os.path.relpath(path, BASE_DIR)

def normalize_route(route):
    return route.replace("\\", "/")

def get_first_id(app_label, model_name):
    try:
        Model = apps.get_model(app_label, model_name)
        obj = Model.objects.order_by("id").first()
        return obj.id if obj else None
    except Exception:
        return None

def get_sample_data_ids():
    return {
        "employee_id": get_first_id("employees", "Employee"),
        "attendance_id": get_first_id("attendance", "Attendance"),
        "charter_id": get_first_id("companies", "WorkCharter"),
        "signature_id": get_first_id("companies", "CharterDigitalSignature"),
        "doc_id": get_first_id("employees", "EmployeeFolder"),
        "request_id": get_first_id("requests_app", "EmployeeRequest"),
        "subscription_id": get_first_id("subscriptions", "CompanySubscription"),
        "branch_id": get_first_id("companies", "Branch"),
        "department_id": get_first_id("companies", "Department"),
        "company_id": get_first_id("companies", "Company"),
    }

def collect_named_patterns():
    resolver = get_resolver()
    results = []

    def walk(patterns, namespaces=None, route_prefix=""):
        namespaces = namespaces or []
        for p in patterns:
            if isinstance(p, URLResolver):
                ns = namespaces[:]
                if p.namespace:
                    ns.append(p.namespace)
                walk(p.url_patterns, ns, route_prefix + str(p.pattern))
            elif isinstance(p, URLPattern):
                name = p.name
                if not name:
                    continue

                full_name = ":".join(namespaces + [name]) if namespaces else name
                namespace = namespaces[0] if namespaces else ""
                route_text = route_prefix + str(p.pattern)

                # احنا نهتم فقط بالأجزاء الأساسية
                if namespace and namespace not in ALLOWED_APP_NAMESPACES:
                    continue

                results.append({
                    "name": name,
                    "full_name": full_name,
                    "namespace": namespace,
                    "route": normalize_route(route_text),
                    "converters": list(getattr(p.pattern, "converters", {}).keys()),
                })

    walk(resolver.url_patterns)
    return results

def build_kwargs(route_info, ids_map):
    kwargs = {}
    for key in route_info["converters"]:
        low = key.lower()

        if low in SPECIAL_STRING_KWARGS:
            kwargs[key] = SPECIAL_STRING_KWARGS[low]
            continue

        if low in ("pk", "id"):
            route_name = route_info["full_name"]
            route_text = route_info["route"]

            if "employees" in route_name or "employees/" in route_text:
                if "folder/" in route_text and ids_map["employee_id"]:
                    kwargs[key] = ids_map["employee_id"]
                elif "profile" in route_text and ids_map["employee_id"]:
                    kwargs[key] = ids_map["employee_id"]
                elif ids_map["employee_id"]:
                    kwargs[key] = ids_map["employee_id"]
                else:
                    return None

            elif "attendance" in route_name or "attendance/" in route_text:
                if "employee" in route_text and ids_map["employee_id"]:
                    kwargs[key] = ids_map["employee_id"]
                elif ids_map["attendance_id"]:
                    kwargs[key] = ids_map["attendance_id"]
                else:
                    return None

            elif "charter" in route_text and ids_map["charter_id"]:
                kwargs[key] = ids_map["charter_id"]

            elif "signature" in route_text and ids_map["signature_id"]:
                kwargs[key] = ids_map["signature_id"]

            elif "requests" in route_text and ids_map["request_id"]:
                kwargs[key] = ids_map["request_id"]

            elif "subscriptions" in route_text and ids_map["subscription_id"]:
                kwargs[key] = ids_map["subscription_id"]

            elif "companies" in route_text and ids_map["company_id"]:
                kwargs[key] = ids_map["company_id"]

            else:
                return None
            continue

        if low == "employee_id":
            if ids_map["employee_id"]:
                kwargs[key] = ids_map["employee_id"]
            else:
                return None
            continue

        if low == "charter_id":
            if ids_map["charter_id"]:
                kwargs[key] = ids_map["charter_id"]
            else:
                return None
            continue

        if low == "signature_id":
            if ids_map["signature_id"]:
                kwargs[key] = ids_map["signature_id"]
            else:
                return None
            continue

        if low == "doc_id":
            if ids_map["doc_id"]:
                kwargs[key] = ids_map["doc_id"]
            else:
                return None
            continue

        if low == "request_id":
            if ids_map["request_id"]:
                kwargs[key] = ids_map["request_id"]
            else:
                return None
            continue

        if low == "branch_id":
            if ids_map["branch_id"]:
                kwargs[key] = ids_map["branch_id"]
            else:
                return None
            continue

        if low == "department_id":
            if ids_map["department_id"]:
                kwargs[key] = ids_map["department_id"]
            else:
                return None
            continue

        if low == "subscription_id":
            if ids_map["subscription_id"]:
                kwargs[key] = ids_map["subscription_id"]
            else:
                return None
            continue

        # أي converter غير مدعوم حاليًا
        return None

    return kwargs

def is_destructive(route_info, path):
    text = (route_info["full_name"] + " " + route_info["route"] + " " + path).lower()
    return any(k in text for k in DESTRUCTIVE_KEYWORDS)

def get_role_users():
    User = get_user_model()
    role_map = {"anonymous": None}

    # super admin
    role_map["super_admin"] = User.objects.filter(is_superuser=True).order_by("id").first()

    # custom roles
    for role_name in ["company_admin", "hr_manager", "manager", "employee"]:
        try:
            role_map[role_name] = User.objects.filter(role=role_name).order_by("id").first()
        except Exception:
            role_map[role_name] = None

    # field employee
    try:
        Employee = apps.get_model("employees", "Employee")
        field_emp = Employee.objects.filter(is_field_worker=True).exclude(user__isnull=True).select_related("user").order_by("id").first()
        role_map["field_employee"] = field_emp.user if field_emp else None
    except Exception:
        role_map["field_employee"] = None

    return role_map

def scan_routes():
    ids_map = get_sample_data_ids()
    patterns = collect_named_patterns()
    role_users = get_role_users()

    results = []
    summary = defaultdict(lambda: defaultdict(int))

    for role_name, user in role_users.items():
        client = Client()
        if user is not None:
            try:
                client.force_login(user)
            except Exception:
                pass

        for route_info in patterns:
            full_name = route_info["full_name"]

            # reverse
            try:
                kwargs = build_kwargs(route_info, ids_map)
                if kwargs is None and route_info["converters"]:
                    results.append({
                        "role": role_name,
                        "route_name": full_name,
                        "path": "",
                        "status": "UNRESOLVED",
                        "code": "",
                        "note": f"Missing sample kwargs: {route_info['converters']}",
                    })
                    summary[role_name]["UNRESOLVED"] += 1
                    continue

                path = reverse(full_name, kwargs=kwargs or None)
            except NoReverseMatch as e:
                results.append({
                    "role": role_name,
                    "route_name": full_name,
                    "path": "",
                    "status": "UNRESOLVED",
                    "code": "",
                    "note": f"reverse error: {e}",
                })
                summary[role_name]["UNRESOLVED"] += 1
                continue
            except Exception as e:
                results.append({
                    "role": role_name,
                    "route_name": full_name,
                    "path": "",
                    "status": "ERROR",
                    "code": "",
                    "note": f"unexpected reverse error: {e}",
                })
                summary[role_name]["ERROR"] += 1
                continue

            if is_destructive(route_info, path):
                results.append({
                    "role": role_name,
                    "route_name": full_name,
                    "path": path,
                    "status": "SKIPPED",
                    "code": "",
                    "note": "Destructive or special route — skipped for safety",
                })
                summary[role_name]["SKIPPED"] += 1
                continue

            try:
                response = client.get(path, follow=False)
                code = response.status_code
                if code == 200:
                    status = "OK"
                elif code in (301, 302):
                    status = "REDIRECT"
                elif code == 403:
                    status = "FORBIDDEN"
                elif code == 404:
                    status = "NOT_FOUND"
                elif code >= 500:
                    status = "SERVER_ERROR"
                else:
                    status = f"HTTP_{code}"

                results.append({
                    "role": role_name,
                    "route_name": full_name,
                    "path": path,
                    "status": status,
                    "code": code,
                    "note": "",
                })
                summary[role_name][status] += 1

            except Exception as e:
                results.append({
                    "role": role_name,
                    "route_name": full_name,
                    "path": path,
                    "status": "EXCEPTION",
                    "code": "",
                    "note": str(e),
                })
                summary[role_name]["EXCEPTION"] += 1

    return results, summary, role_users

def write_csv(results):
    with open(SCAN_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["role", "route_name", "path", "status", "code", "note"]
        )
        writer.writeheader()
        writer.writerows(results)

def write_md_report(results, summary, role_users):
    lines = []
    lines.append("# تقرير الفحص الآلي — MotionHR")
    lines.append("")
    lines.append("هذا التقرير نتج عن فحص آلي للـ named URLs باستخدام Django Test Client.")
    lines.append("")
    lines.append("## المستخدمون الذين تم الفحص بهم")
    lines.append("")
    for role_name, user in role_users.items():
        if user is None:
            lines.append(f"- **{role_name}**: غير متوفر")
        else:
            username = getattr(user, "username", "—")
            lines.append(f"- **{role_name}**: {username}")
    lines.append("")
    lines.append("## الملخص")
    lines.append("")

    for role_name in role_users.keys():
        role_summary = summary.get(role_name, {})
        total = sum(role_summary.values())
        lines.append(f"### {role_name}")
        lines.append(f"- إجمالي الفحوصات: **{total}**")
        for key in sorted(role_summary.keys()):
            lines.append(f"  - {key}: {role_summary[key]}")
        lines.append("")

    lines.append("## تفاصيل المشاكل فقط")
    lines.append("")

    bad_statuses = {"UNRESOLVED", "ERROR", "EXCEPTION", "SERVER_ERROR", "NOT_FOUND"}
    for row in results:
        if row["status"] in bad_statuses:
            lines.append(f"- **{row['role']}** | `{row['route_name']}` | `{row['path']}` | **{row['status']}** | {row['note']}")

    lines.append("")
    lines.append("## ملاحظات")
    lines.append("")
    lines.append("- `SKIPPED` = Route حساس أو destructive ولم يتم الضغط عليه آليًا حفاظًا على البيانات.")
    lines.append("- `REDIRECT` غالبًا طبيعي لو الصفحة تحتاج تسجيل دخول أو تعيد التوجيه.")
    lines.append("- `FORBIDDEN` قد يكون طبيعي حسب الصلاحيات.")
    lines.append("- الأداة لا تضغط POST destructive تلقائيًا.")
    lines.append("")

    with open(SCAN_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def write_manual_checklist(role_users, results):
    # نجمع أفضل routes لكل role
    role_routes_ok = defaultdict(list)
    role_routes_review = defaultdict(list)

    for row in results:
        role = row["role"]
        if row["status"] == "OK":
            role_routes_ok[role].append((row["route_name"], row["path"]))
        elif row["status"] in {"REDIRECT", "FORBIDDEN", "SKIPPED"}:
            role_routes_review[role].append((row["route_name"], row["path"], row["status"]))

    lines = []
    lines.append("# Manual QA Checklist — MotionHR")
    lines.append("")
    lines.append("استخدم هذه القائمة للتجربة اليدوية بجانب الفحص الآلي.")
    lines.append("")
    lines.append("## 1) قواعد التنفيذ")
    lines.append("")
    lines.append("- افتح كل رابط وسجّل هل الصفحة منطقية أم لا.")
    lines.append("- جرّب كل زرار ظاهر في الصفحة (عرض / حفظ / رجوع / طباعة / تصدير).")
    lines.append("- أي Route حالته `SKIPPED` أو `REDIRECT` أو `FORBIDDEN` يحتاج مراجعة يدوية.")
    lines.append("- علّم كل بند بـ ✅ أو ❌ أثناء الاختبار.")
    lines.append("")

    lines.append("## 2) بيانات المستخدمين المتاحة")
    lines.append("")
    for role_name, user in role_users.items():
        if user is None:
            lines.append(f"- **{role_name}**: غير متوفر")
        else:
            lines.append(f"- **{role_name}**: `{getattr(user, 'username', '—')}`")
    lines.append("")

    # Role sections
    for role_name in ["super_admin", "company_admin", "hr_manager", "manager", "employee", "field_employee"]:
        lines.append(f"## اختبار Role: {role_name}")
        lines.append("")

        if role_users.get(role_name) is None:
            lines.append("- لا يوجد مستخدم متاح لهذا الدور حاليًا.")
            lines.append("")
            continue

        lines.append("### أ) فحص عام")
        lines.append("- [ ] تسجيل الدخول")
        lines.append("- [ ] فتح Dashboard")
        lines.append("- [ ] فتح البروفايل")
        lines.append("- [ ] فتح تغيير كلمة المرور (إن وجدت)")
        lines.append("- [ ] تسجيل الخروج")
        lines.append("")

        lines.append("### ب) الصفحات التي فتحت آليًا بنجاح")
        lines.append("")
        ok_items = sorted(set(role_routes_ok.get(role_name, [])), key=lambda x: x[1])
        if not ok_items:
            lines.append("- لا توجد صفحات OK مسجلة آليًا.")
        else:
            for route_name, path in ok_items:
                lines.append(f"- [ ] `{path}` — ({route_name})")
        lines.append("")

        lines.append("### ج) صفحات تحتاج مراجعة خاصة")
        lines.append("")
        review_items = sorted(set(role_routes_review.get(role_name, [])), key=lambda x: (x[2], x[1]))
        if not review_items:
            lines.append("- لا توجد صفحات مراجعة خاصة.")
        else:
            for route_name, path, status in review_items:
                lines.append(f"- [ ] `{path}` — ({route_name}) — **{status}**")
        lines.append("")

        lines.append("### د) سيناريوهات مهمة لهذا الدور")
        lines.append("")
        if role_name == "company_admin":
            lines.extend([
                "- [ ] إعداد الشركة والفروع والإدارات",
                "- [ ] تجربة صفحة الهيكل الوظيفي",
                "- [ ] إضافة موظف جديد",
                "- [ ] فتح ملف المستندات لموظف",
                "- [ ] تجربة الحضور / الخريطة / التتبع",
                "- [ ] تجربة الإجازات والطلبات",
                "- [ ] فتح كل التقارير والتصدير",
                "- [ ] تجربة صفحات الـ Add-ons / Upsell",
            ])
        elif role_name == "hr_manager":
            lines.extend([
                "- [ ] إضافة / تعديل موظف",
                "- [ ] مراجعة الحضور",
                "- [ ] مراجعة الإجازات",
                "- [ ] مراجعة الطلبات",
                "- [ ] فتح ملف شامل لموظف",
                "- [ ] رفع مستندات موظف",
            ])
        elif role_name == "manager":
            lines.extend([
                "- [ ] مراجعة فريقه فقط",
                "- [ ] الموافقة على الطلبات",
                "- [ ] مراجعة الحضور الخاص بفريقه",
                "- [ ] متابعة الموظفين الميدانيين إن وُجد",
            ])
        elif role_name == "employee":
            lines.extend([
                "- [ ] تسجيل حضور/انصراف",
                "- [ ] تقديم طلب جديد",
                "- [ ] تقديم طلب إجازة",
                "- [ ] رؤية رصيد الإجازات",
                "- [ ] مراجعة إشعاراته",
            ])
        elif role_name == "field_employee":
            lines.extend([
                "- [ ] تسجيل حضور GPS",
                "- [ ] إرسال موقع / تتبع",
                "- [ ] تسجيل زيارة ميدانية",
                "- [ ] مراجعة الإشعارات المرتبطة بالتتبع",
            ])
        else:
            lines.extend([
                "- [ ] مراجعة Admin / الشاشات الإدارية",
                "- [ ] التحقق من أن كل التطبيقات ظاهرة وتفتح",
            ])
        lines.append("")

    lines.append("## 3) سيناريوهات شاملة مشتركة")
    lines.append("")
    lines.extend([
        "- [ ] Landing page تعمل",
        "- [ ] Pricing page تعمل",
        "- [ ] Free Trial page تعمل",
        "- [ ] التسجيل في Free Trial يعمل",
        "- [ ] صفحة success بعد التجربة تعمل",
        "- [ ] الدخول ببيانات التجربة يعمل",
        "- [ ] لا توجد صفحات 500 أثناء السيناريو الرئيسي",
        "- [ ] التصدير Excel يعمل",
        "- [ ] التصدير PDF يعمل",
        "- [ ] الطباعة تعمل",
    ])
    lines.append("")

    with open(CHECKLIST_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

print("=" * 70)
print("Patch 49N — System Scan + QA Checklist")
print("=" * 70)

results, summary, role_users = scan_routes()
write_csv(results)
write_md_report(results, summary, role_users)
write_manual_checklist(role_users, results)

print(f"\n✅ تم إنشاء التقارير:")
print(f"   - {safe_rel(SCAN_MD)}")
print(f"   - {safe_rel(SCAN_CSV)}")
print(f"   - {safe_rel(CHECKLIST_MD)}")

# Quick terminal summary
for role_name in role_users.keys():
    role_summary = summary.get(role_name, {})
    total = sum(role_summary.values())
    print(f"\n[{role_name}] total={total}")
    for key in sorted(role_summary.keys()):
        print(f"  {key}: {role_summary[key]}")

print("\n" + "=" * 70)
print("✅ Patch 49N اكتمل")
print("=" * 70)
print("""
اقرأ الملفات التالية:
  1) _patches/_reports/49n_scan_report.md
  2) _patches/_reports/49n_scan_results.csv
  3) _patches/_reports/49n_manual_qa_checklist.md

مهم:
- التقرير الآلي يكشف الصفحات الواقعة والمكسورة
- الـ Checklist تكمل الباقي يدويًا
- الأزرار POST الحساسة يتم تعليمها SKIPPED ولا يتم الضغط عليها تلقائيًا
""")