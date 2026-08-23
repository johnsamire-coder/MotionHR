import pathlib, re

BASE = pathlib.Path('.')
content = (BASE / 'leaves' / 'signals.py').read_text(encoding='utf-8')

match = re.search(r'def _get_entitlement_days\(.*?\):.*?(?=\ndef |\Z)', content, re.DOTALL)
if match:
    print("=== Function _get_entitlement_days ===")
    print(match.group(0))
else:
    print("_get_entitlement_days not found")

