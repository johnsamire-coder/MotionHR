import pathlib, re

BASE = pathlib.Path('.')
content = (BASE / 'attendance' / 'payroll_rules.py').read_text(encoding='utf-8')

match = re.search(r'def _apply_absence_rule\(.*?\):.*?(?=\ndef |\Z)', content, re.DOTALL)
if match:
    print("=== Function _apply_absence_rule ===")
    print(match.group(0))
else:
    print("_apply_absence_rule not found")

