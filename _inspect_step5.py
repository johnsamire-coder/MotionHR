import pathlib, re

BASE = pathlib.Path('.')

print("=== 1. Checking LeavePolicyTier Model in leaves/models.py ===")
models_content = (BASE / 'leaves' / 'models.py').read_text(encoding='utf-8')
match = re.search(r'class LeavePolicyTier\(.*?\):.*?(?=\nclass |\Z)', models_content, re.DOTALL)
if match:
    print(match.group(0))
else:
    print("LeavePolicyTier not found")

print("\n=== 2. Checking Leave Balance Calculation in leaves/ ===")
for f in ['leaves/api_leave_policy.py', 'leaves/views.py', 'leaves/signals.py']:
    p = BASE / f
    if p.exists():
        text = p.read_text(encoding='utf-8')
        matches = [line.strip() for line in text.splitlines() if 'balance' in line.lower() or 'entitlement' in line.lower()][:10]
        print(f"--- File: {f} ---")
        print('\n'.join(matches))

