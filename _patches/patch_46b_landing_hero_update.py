#!/usr/bin/env python3
"""
Patch 46b: Landing Hero Text Update
=====================================
- شيل "صغيرة ومتوسطة"
- عدّل الأرقام لتكون عامة
- خلي الرسالة مناسبة لكل أحجام الشركات
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
print("  Patch 46b: Landing Hero Update")
print("=" * 60)

home_path = os.path.join(BASE_DIR, "templates", "landing", "home.html")
content = read_file(home_path)

# ═══ تعديل 1: Hero subtitle ═══
old_subtitle = """MotionHR نظام إدارة موارد بشرية عصري مصمم للشركات الصغيرة والمتوسطة
          في مصر والعالم العربي. تتبع حضور موظفيك بالـ GPS، وتابع الميدانيين
          على الخريطة، وأدِر الإجازات والتقارير بسهولة تامة."""

new_subtitle = """MotionHR نظام إدارة موارد بشرية عصري مصمم لكل الشركات
          في مصر والعالم العربي. تتبع حضور موظفيك بالـ GPS، وتابع الميدانيين
          على الخريطة، وأدِر الإجازات والتقارير بسهولة تامة — مهما كان حجم فريقك."""

if old_subtitle in content:
    content = content.replace(old_subtitle, new_subtitle)
    print("  ✅ تم تعديل Hero subtitle")
else:
    # نبحث بنص أقصر
    content = content.replace(
        "مصمم للشركات الصغيرة والمتوسطة",
        "مصمم لكل الشركات"
    )
    print("  ✅ تم تعديل النص (طريقة بديلة)")

# ═══ تعديل 2: Hero badge ═══
content = content.replace(
    "نظام HR الأذكى للشركات العربية",
    "نظام HR الأذكى لإدارة فريقك"
)

# ═══ تعديل 3: الأرقام ═══
old_stats = '{"value": "10-100",  "label": "موظف"}'
new_stats = '{"value": "∞",       "label": "بدون حد للموظفين"}'

if old_stats in content:
    content = content.replace(old_stats, new_stats)
    print("  ✅ تم تعديل الإحصائيات")
else:
    # نبحث في الـ template مباشرة
    content = content.replace("10-100", "∞")
    content = content.replace('"موظف"', '"بدون حد للموظفين"')
    print("  ✅ تم تعديل الأرقام (طريقة بديلة)")

# ═══ تعديل 4: أي ذكر تاني لـ "صغيرة ومتوسطة" ═══
content = content.replace(
    "الشركات الصغيرة والمتوسطة",
    "الشركات بمختلف أحجامها"
)

# ═══ تعديل 5: meta description ═══
content = content.replace(
    'content="MotionHR - نظام إدارة الموارد البشرية الأذكى للشركات الصغيرة والمتوسطة في مصر والعالم العربي"',
    'content="MotionHR - نظام إدارة الموارد البشرية الأذكى لكل الشركات في مصر والعالم العربي"'
)

write_file(home_path, content)

# ═══ تحديث about.html كمان ═══
print("\n🔧 تحديث about.html...")

about_path = os.path.join(BASE_DIR, "templates", "landing", "about.html")
about = read_file(about_path)

about = about.replace(
    "الشركات العربية الصغيرة والمتوسطة",
    "الشركات العربية بمختلف أحجامها"
)
about = about.replace(
    "الشركات الصغيرة والمتوسطة",
    "الشركات بمختلف أحجامها"
)

write_file(about_path, about)

# ═══ تحديث views.py ═══
print("\n🔧 تحديث landing/views.py...")

views_path = os.path.join(BASE_DIR, "landing", "views.py")
views = read_file(views_path)

views = views.replace(
    "الشركات الصغيرة والمتوسطة",
    "الشركات بمختلف أحجامها"
)
views = views.replace(
    '{"value": "10-100",  "label": "موظف"}',
    '{"value": "\\u221e",  "label": "بدون حد للموظفين"}'
)

write_file(views_path, views)

print("\n" + "=" * 60)
print("  ✅ Patch 46b اكتمل!")
print("=" * 60)
print("""
اللي اتعدل:
  ✅ شلنا "صغيرة ومتوسطة" من كل مكان
  ✅ "10-100" بقت "بدون حد للموظفين"
  ✅ الرسالة بقت عامة لكل أحجام الشركات
  ✅ meta description محدث
  ✅ about.html محدث
  ✅ views.py محدث

جرب:
  http://127.0.0.1:8000/
  http://127.0.0.1:8000/about/
""")