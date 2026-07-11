#!/usr/bin/env python3
"""
Patch 30b: Fix Check-in page for employees
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 30b: Fix Check-in")
print("=" * 60)

# ═══════════════════════════════════════════
# تحديث attendance/views.py
# إضافة flag لإخفاء الخريطة عن الموظف
# ═══════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

# نبحث عن check_in view ونضيف show_map في الـ context
if "show_map" not in views:
    # نبحث عن الـ context في check_in view
    # نضيف show_map حسب الدور
    old_text = "return render(request, 'attendance/check_in.html'"
    new_text = """# هل نعرض الخريطة؟
    show_map = getattr(request.user, 'role', 'employee') != 'employee'
    if 'context' in dir():
        context['show_map'] = show_map
    else:
        context = {'show_map': show_map}

    return render(request, 'attendance/check_in.html'"""

    if old_text in views:
        views = views.replace(old_text, new_text, 1)
        write_file(views_path, views)
        print("  ✅ تم إضافة show_map في الـ view")
    else:
        print("  ℹ️  مش لاقي النص بالظبط - هنعدل يدوي")
else:
    print("  ℹ️  show_map موجود")


# ═══════════════════════════════════════════
# تحديث check_in.html
# إخفاء الخريطة بناءً على show_map
# ═══════════════════════════════════════════
print("\n🔧 تحديث check_in.html...")

checkin_path = os.path.join(BASE_DIR, "templates", "attendance", "check_in.html")
checkin = read_file(checkin_path)

# نلف الخريطة بـ if show_map
if "show_map" not in checkin:
    # نبحث عن div الخريطة
    map_markers = [
        'id="map"',
        "id='map'",
        'id="mapContainer"',
        'class="map-container"',
        'id="attendanceMap"',
    ]

    found_map = False
    for marker in map_markers:
        if marker in checkin:
            # نلف أقرب div parent بـ {% if show_map %}
            idx = checkin.find(marker)
            # نرجع لأقرب <div قبله
            div_start = checkin.rfind("<div", 0, idx)
            if div_start != -1:
                checkin = (
                    checkin[:div_start]
                    + "\n{% if show_map %}\n"
                    + checkin[div_start:]
                )
                # نلاقي إغلاق الـ div ده
                # نبحث عن أول </div> بعد الخريطة
                map_end = checkin.find("</div>", idx + 100)
                if map_end != -1:
                    checkin = (
                        checkin[:map_end + 6]
                        + "\n{% endif %}\n"
                        + checkin[map_end + 6:]
                    )
                    found_map = True
                    break

    if found_map:
        write_file(checkin_path, checkin)
        print("  ✅ الخريطة مخفية عن الموظف")
    else:
        print("  ⚠️  مش لاقي div الخريطة - هنعمل CSS fallback")

        # CSS Fallback
        css_fix = """
<style>
  .role-employee #map,
  .role-employee .map-container,
  .role-employee .map-section,
  .role-employee [id*="map"] {
    display: none !important;
  }
</style>
"""
        # نضيف class على body حسب الدور
        if "<body" in checkin:
            checkin = checkin.replace(
                "<body",
                '<body class="role-{{ request.user.role }}"'
            )
        elif "{% block content %}" in checkin:
            checkin = checkin.replace(
                "{% block content %}",
                css_fix + "\n{% block content %}"
            )

        write_file(checkin_path, checkin)
        print("  ✅ CSS fallback لإخفاء الخريطة")


print("\n" + "=" * 60)
print("  ✅ Patch 30b اكتمل!")
print("=" * 60)
print("""
جرب:
  ادخل بـ emp10003 / Emp@12345
  افتح تسجيل الحضور
  الخريطة المفروض تختفي
""")