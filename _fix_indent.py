import pathlib, re

BASE = pathlib.Path('.')
models_path = BASE / 'leaves' / 'models.py'
content = models_path.read_text(encoding='utf-8')

# تنظيف أي أسطر مضافة بالخطأ
lines = content.splitlines()
clean_lines = [l for l in lines if 'require_reason' not in l and 'is_excused_absence' not in l]

new_lines = []
in_leave_type = False
added = False

for line in clean_lines:
    if line.strip().startswith('class LeaveType'):
        in_leave_type = True
    elif in_leave_type and line.strip().startswith('class '):
        in_leave_type = False
    
    # نضيف الحقول بعد color أو is_paid داخل LeaveType
    if in_leave_type and not added and ('color' in line or 'is_paid' in line):
        new_lines.append(line)
        new_lines.append('    require_reason = models.BooleanField(default=False, verbose_name="السبب إجباري")')
        new_lines.append('    is_excused_absence = models.BooleanField(default=False, verbose_name="غياب بعذر")')
        added = True
        continue
    new_lines.append(line)

models_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
print("[OK] leaves/models.py cleaned and fields added with exact 4-space indentation.")
