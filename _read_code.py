import pathlib

BASE = pathlib.Path('.')

def show_file(fp, max_lines=80, label=""):
    p = BASE / fp
    if not p.exists():
        print(f"\n[!] {fp} NOT FOUND")
        return
    content = p.read_text(encoding='utf-8')
    lines = content.splitlines()
    print(f"\n{'='*60}")
    print(f"FILE: {fp} ({len(lines)} lines) {label}")
    print(f"{'='*60}")
    print('\n'.join(lines[:max_lines]))
    if len(lines) > max_lines:
        print(f"\n... ({len(lines) - max_lines} more lines)")

# 1) attendance/api_mobile.py — أول 100 سطر عشان نشوف الـ serializers والـ logic
show_file('attendance/api_mobile.py', 100, '— MOBILE API')

# 2) attendance/views.py — أول 80 سطر
show_file('attendance/views.py', 80, '— VIEWS')

# 3) leaves/views.py — أول 80 سطر
show_file('leaves/views.py', 80, '— LEAVES VIEWS')

# 4) attendance/urls.py — كامل
show_file('attendance/urls.py', 200, '— URLS')

# 5) leaves/urls.py — كامل
show_file('leaves/urls.py', 100, '— LEAVES URLS')

