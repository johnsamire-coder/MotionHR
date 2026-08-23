import os, sys, pathlib, re

BASE = pathlib.Path('.')

# ============================================================
# 1) تعديل leaves/models.py
# ============================================================
models_path = BASE / 'leaves' / 'models.py'
content = models_path.read_text(encoding='utf-8')

if 'require_reason' not in content:
    target = 'color            = models.CharField('
    addition = """    require_reason   = models.BooleanField(default=False, verbose_name="السبب إجباري")
    is_excused_absence = models.BooleanField(default=False, verbose_name="غياب بعذر")
"""
    if target in content:
        content = content.replace(target, addition + target, 1)
        models_path.write_text(content, encoding='utf-8')
        print("[OK] leaves/models.py: Added require_reason & is_excused_absence")
    else:
        # لو النمط مختلف نضيفها بعد is_active
        content = content.replace('is_active =', addition + '    is_active =', 1)
        models_path.write_text(content, encoding='utf-8')
        print("[OK] leaves/models.py: Added fields before is_active")
else:
    print("[SKIP] leaves/models.py: Fields already exist")

# ============================================================
# 2) تعديل attendance/api_mobile_requests.py
# ============================================================
api_path = BASE / 'attendance' / 'api_mobile_requests.py'
api_content = api_path.read_text(encoding='utf-8')

# أ) تحديث mobile_leave_types لترجع الحقول للفرونت والموبايل
types_pattern = r'("description":\s*lt\.description\s*or\s*"",)'
types_addition = r'\1\n            "require_reason": getattr(lt, "require_reason", False),\n            "is_excused_absence": getattr(lt, "is_excused_absence", False),'

if '"require_reason"' not in api_content:
    api_content = re.sub(types_pattern, types_addition, api_content)
    print("[OK] attendance/api_mobile_requests.py: Updated mobile_leave_types response")

# ب) تحديث mobile_leave_request للتحقق من وجود السبب
old_reason_logic = """    # REQ-1: السبب اختياري - نحط اسم النوع
    if not reason:
        try:
            _lt = LeaveType._base_manager.get(id=leave_type_id, company=employee.company)
            reason = _lt.name or 'إجازة'
        except Exception:
            reason = 'إجازة'"""

new_reason_logic = """    # التحقق من إجبارية السبب للغياب بعذر
    try:
        _check_lt = LeaveType._base_manager.get(id=leave_type_id, company=employee.company)
        if (getattr(_check_lt, "require_reason", False) or getattr(_check_lt, "is_excused_absence", False)) and not reason:
            return Response({
                'success': False,
                'message': 'يجب كتابة سبب الغياب بالتفصيل لهذا النوع من الإجازات'
            }, status=400)
        if not reason:
            reason = _check_lt.name or 'إجازة'
    except Exception:
        if not reason:
            reason = 'إجازة'"""

if 'يجب كتابة سبب الغياب بالتفصيل' not in api_content:
    if old_reason_logic in api_content:
        api_content = api_content.replace(old_reason_logic, new_reason_logic, 1)
        print("[OK] attendance/api_mobile_requests.py: Added mandatory reason validation")
    else:
        print("[!] Warning: Could not match exact old_reason_logic block")

api_path.write_text(api_content, encoding='utf-8')

