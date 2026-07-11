"""
Patch 49d — Smart Schedule Assignment UI

الهدف:
- تحسين واجهة تكليفات جدول العمل حسب work_mode
- لو Fixed → إظهار حقول البداية/النهاية المناسبة فقط
- لو Flexible → إظهار إجمالي الساعات فقط
- لو Split/Mixed → إظهار حقول الجزء 1 / الجزء 2
- الحقول غير المطلوبة تختفي ديناميكيًا

مهم:
- الباتش يقرأ DailyAssignment model الحقيقي
- ويحدد أسماء الحقول الموجودة فعليًا
- ويحدث template فقط
"""

import os
import sys
import shutil
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")
django.setup()


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
print("Patch 49d — Smart Schedule Assignment UI")
print("=" * 60)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

template_path = "templates/attendance/assignment_form.html"
template_full = os.path.join(BASE_DIR, template_path)

if os.path.exists(template_full):
    shutil.copy2(
        template_full,
        os.path.join(backup_dir, "attendance_assignment_form_before_patch_49d.html.bak")
    )
    print("✅ Backup created: _patches/_backups/attendance_assignment_form_before_patch_49d.html.bak")

# ────────────────────────────────────────────────────────────
# Inspect DailyAssignment model
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: فحص حقول DailyAssignment")

from attendance.models import DailyAssignment

field_names = []
for f in DailyAssignment._meta.get_fields():
    if getattr(f, "concrete", False) and not getattr(f, "many_to_many", False):
        field_names.append(f.name)

print("   DailyAssignment fields:")
for name in field_names:
    print("   -", name)

work_mode_choices = []
try:
    work_mode_field = DailyAssignment._meta.get_field("work_mode")
    work_mode_choices = [choice[0] for choice in getattr(work_mode_field, "choices", [])]
except Exception:
    pass

print(f"   work_mode choices: {work_mode_choices}")

# ────────────────────────────────────────────────────────────
# Smart field detection
# ────────────────────────────────────────────────────────────
def has_any(name, tokens):
    n = name.lower()
    return any(t in n for t in tokens)

def not_any(name, tokens):
    n = name.lower()
    return all(t not in n for t in tokens)

# إجمالي الساعات / مدة
hours_fields = [
    n for n in field_names
    if has_any(n, ["hour", "hours", "duration", "total"]) and not_any(n, ["overtime"])
]

# الجزء الأول
part1_fields = [
    n for n in field_names
    if has_any(n, ["part1", "part_1", "first_part", "first", "segment1", "segment_1", "morning"])
]

# الجزء الثاني
part2_fields = [
    n for n in field_names
    if has_any(n, ["part2", "part_2", "second_part", "second", "segment2", "segment_2", "evening"])
]

# البداية / النهاية الثابتة
fixed_time_fields = [
    n for n in field_names
    if has_any(n, ["start", "from", "begin", "end", "to", "finish"])
    and not has_any(n, ["date", "part1", "part_1", "part2", "part_2", "first", "second", "segment1", "segment2"])
]

# لو موديلك فيه حقول split بأسماء غير قياسية لكن فيها part
extra_split_fields = [
    n for n in field_names
    if has_any(n, ["split"]) and n not in part1_fields and n not in part2_fields
]

# استبعاد work_mode نفسه وأشياء لا نريد إخفاءها
excluded_fields = {
    "id", "company", "created_at", "updated_at", "created_by", "updated_by",
    "employee", "date", "day_type", "work_mode", "notes"
}

hours_fields = [n for n in hours_fields if n not in excluded_fields]
part1_fields = [n for n in part1_fields if n not in excluded_fields]
part2_fields = [n for n in part2_fields if n not in excluded_fields]
fixed_time_fields = [n for n in fixed_time_fields if n not in excluded_fields]
extra_split_fields = [n for n in extra_split_fields if n not in excluded_fields]

print("\n📌 Step 2: الحقول المكتشفة")
print("   fixed_time_fields =", fixed_time_fields)
print("   hours_fields      =", hours_fields)
print("   part1_fields      =", part1_fields)
print("   part2_fields      =", part2_fields)
print("   extra_split_fields=", extra_split_fields)

# ────────────────────────────────────────────────────────────
# Update template
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: تحديث assignment_form.html")

template_content = read_file(template_path)
if template_content is None:
    raise SystemExit("❌ ملف templates/attendance/assignment_form.html غير موجود")

css_block = """
<style id="patch49d-schedule-style">
  .schedule-mode-note {
    border: 1px solid #bae6fd;
    background: #f0f9ff;
    border-radius: 14px;
    padding: 12px 14px;
    color: #0c4a6e;
    font-size: .9rem;
    margin-bottom: 1rem;
  }
  .schedule-mode-note strong {
    color: #075985;
  }
</style>
"""

js_block = f"""
<script id="patch49d-schedule-script">
(function() {{
  const workMode = document.querySelector('[name="work_mode"]');
  if (!workMode) return;

  const FIXED_FIELDS = {fixed_time_fields!r};
  const HOURS_FIELDS = {hours_fields!r};
  const PART1_FIELDS = {part1_fields!r};
  const PART2_FIELDS = {part2_fields!r};
  const EXTRA_SPLIT_FIELDS = {extra_split_fields!r};

  function findWrap(input) {{
    if (!input) return null;
    return input.closest('.field-box')
      || input.closest('[class*="col-"]')
      || input.closest('.mb-3')
      || input.closest('.form-group')
      || input.parentElement;
  }}

  function findInputByName(name) {{
    return document.querySelector('[name="' + name + '"]');
  }}

  function setFieldVisibility(fieldNames, show) {{
    fieldNames.forEach(function(name) {{
      const input = findInputByName(name);
      if (!input) return;
      const wrap = findWrap(input);
      if (!wrap) return;
      wrap.style.display = show ? '' : 'none';
    }});
  }}

  function ensureModeNote() {{
    let note = document.getElementById('scheduleModeNote');
    if (note) return note;

    note = document.createElement('div');
    note.id = 'scheduleModeNote';
    note.className = 'schedule-mode-note';

    const wrap = findWrap(workMode);
    if (wrap && wrap.parentElement) {{
      wrap.parentElement.insertBefore(note, wrap.nextSibling);
    }} else {{
      workMode.parentElement.appendChild(note);
    }}
    return note;
  }}

  function updateNote(text) {{
    const note = ensureModeNote();
    note.innerHTML = text;
  }}

  function showAllRelevant() {{
    setFieldVisibility(FIXED_FIELDS, true);
    setFieldVisibility(HOURS_FIELDS, true);
    setFieldVisibility(PART1_FIELDS, true);
    setFieldVisibility(PART2_FIELDS, true);
    setFieldVisibility(EXTRA_SPLIT_FIELDS, true);
  }}

  function applyMode() {{
    const mode = String(workMode.value || '').toLowerCase().trim();

    // reset
    showAllRelevant();

    if (!mode) {{
      updateNote('<strong>اختر طريقة التنفيذ:</strong> عند اختيار طريقة التنفيذ سيظهر لك فقط الحقول المناسبة لها.');
      return;
    }}

    // Fixed
    if (mode === 'fixed') {{
      setFieldVisibility(HOURS_FIELDS, false);
      setFieldVisibility(PART1_FIELDS, false);
      setFieldVisibility(PART2_FIELDS, false);
      setFieldVisibility(EXTRA_SPLIT_FIELDS, false);

      updateNote('<strong>تنفيذ ثابت:</strong> تم إظهار حقول البداية والنهاية فقط، وإخفاء الحقول الخاصة بالمرن أو التقسيم.');
      return;
    }}

    // Flexible
    if (mode === 'flexible' || mode === 'flex' || mode === 'flexi' || mode === 'مرن') {{
      setFieldVisibility(FIXED_FIELDS, false);
      setFieldVisibility(PART1_FIELDS, false);
      setFieldVisibility(PART2_FIELDS, false);
      setFieldVisibility(EXTRA_SPLIT_FIELDS, false);

      updateNote('<strong>تنفيذ مرن:</strong> تم إظهار إجمالي الساعات/المدة فقط، وإخفاء البداية والنهاية والتقسيم.');
      return;
    }}

    // Split
    if (mode === 'split') {{
      setFieldVisibility(FIXED_FIELDS, false);
      setFieldVisibility(HOURS_FIELDS, false);

      updateNote('<strong>تنفيذ متقسم:</strong> تم إظهار حقول الجزء الأول والجزء الثاني فقط.');
      return;
    }}

    // Mixed
    if (mode === 'mixed') {{
      setFieldVisibility(HOURS_FIELDS, false);

      updateNote('<strong>تنفيذ مختلط:</strong> تم إظهار الحقول المناسبة للتنفيذ المقسم/المختلط.');
      return;
    }}

    // fallback
    updateNote('<strong>وضع مخصص:</strong> تم الإبقاء على الحقول الظاهرة كما هي لأن طريقة التنفيذ الحالية غير قياسية.');
  }}

  workMode.addEventListener('change', applyMode);
  window.addEventListener('load', applyMode);
}})();
</script>
"""

# Inject CSS once
if "patch49d-schedule-style" not in template_content:
    if "{% block extra_css %}" in template_content:
        template_content = template_content.replace(
            "{% block extra_css %}",
            "{% block extra_css %}\n" + css_block + "\n",
            1
        )
    else:
        template_content += "\n{% block extra_css %}\n" + css_block + "\n{% endblock %}\n"

# Inject JS once
if "patch49d-schedule-script" not in template_content:
    if "{% block extra_js %}" in template_content:
        template_content = template_content.replace(
            "{% block extra_js %}",
            "{% block extra_js %}\n" + js_block + "\n",
            1
        )
    else:
        template_content += "\n{% block extra_js %}\n" + js_block + "\n{% endblock %}\n"

write_file(template_path, template_content)

print("\n" + "=" * 60)
print("✅ Patch 49d اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ فحص موديل DailyAssignment الحقيقي
  ✅ اكتشاف حقول:
     - البداية/النهاية
     - إجمالي الساعات
     - الجزء الأول
     - الجزء الثاني
  ✅ تحديث assignment_form.html بـ UI ذكي حسب work_mode
  ✅ إخفاء/إظهار الحقول ديناميكيًا
  ✅ إنشاء Backup قبل التعديل

مهم:
  ✅ هذا الباتش لا يغير الموديل ولا قاعدة البيانات
  ✅ فقط يحسن UX في شاشة التكليف

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")