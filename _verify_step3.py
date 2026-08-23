import pathlib

content = pathlib.Path('attendance/payroll_rules.py').read_text(encoding='utf-8')
print("=== Verification of _apply_absence_rule ===")
print(f"Uses _base_manager: {'[OK]' if 'AbsenceRule._base_manager' in content else '[X]'}")
print(f"Supports Multiplier (>1 day): {'[OK]' if 'mult = float(rule' in content else '[X]'}")
print(f"Supports Consecutive & Repeated: {'[OK]' if 'rule_c' in content and 'rule_r' in content else '[X]'}")
