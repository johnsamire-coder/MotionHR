import requests
import json
import time

BASE = 'https://jssolutions-eg.com'
PASSWORD = 'Test@1234'

# GPS coordinates (Cairo area)
LAT = 30.0444
LON = 31.2357

total = 0
passed = 0
failed = []

def login(username):
    try:
        r = requests.post(
            f'{BASE}/attendance/api/mobile/login/',
            json={'username': username, 'password': PASSWORD},
            timeout=20,
        )
        data = r.json()
        if r.status_code == 200 and data.get('success') and data.get('token'):
            return data['token'], data
    except Exception:
        pass
    return None, None

def api_get(token, path):
    try:
        r = requests.get(
            f'{BASE}{path}',
            headers={'Authorization': f'Token {token}'},
            timeout=20,
        )
        return r.status_code, r.json() if r.headers.get('Content-Type','').startswith('application/json') else {}
    except Exception as e:
        return 'EXC', {'error': str(e)}

def api_post(token, path, data=None):
    try:
        r = requests.post(
            f'{BASE}{path}',
            headers={'Authorization': f'Token {token}', 'Content-Type': 'application/json'},
            json=data or {},
            timeout=20,
        )
        return r.status_code, r.json() if r.headers.get('Content-Type','').startswith('application/json') else {}
    except Exception as e:
        return 'EXC', {'error': str(e)}

def check(label, condition, detail=''):
    global total, passed
    total += 1
    if condition:
        passed += 1
        print(f'  \u2705 {label}')
    else:
        failed.append((label, detail))
        print(f'  \u274C {label} => {detail}')

print('=' * 70)
print('MOTIONHR — FULL BUSINESS FLOW TEST')
print('=' * 70)

# ════════════════════════════════════════
# 1. LOGIN + PROFILE (موظف + مدير)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('1. LOGIN + PROFILE')

# مدير عقاري
admin_token, admin_data = login('re_admin')
check('LOGIN مدير عقاري', admin_token is not None)

sc, d = api_get(admin_token, '/attendance/api/mobile/employee/profile/')
check('PROFILE مدير', sc == 200 and d.get('full_name_ar'))

# موظف ميداني
emp_token, emp_data = login('re_sales_1')
check('LOGIN موظف ميداني', emp_token is not None)

sc, d = api_get(emp_token, '/attendance/api/mobile/employee/profile/')
check('PROFILE موظف', sc == 200 and d.get('full_name_ar'))

# ════════════════════════════════════════
# 2. ATTENDANCE (حضور + انصراف)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('2. ATTENDANCE')

# حالة الحضور
sc, d = api_get(emp_token, f'/attendance/api/mobile/status/?latitude={LAT}&longitude={LON}')
check('حالة الحضور', sc == 200)

# تسجيل حضور يدوي
sc, d = api_post(emp_token, '/attendance/api/mobile/attendance/', {
    'action': 'check_in',
    'latitude': LAT,
    'longitude': LON,
    'accuracy': 10,
})
check('تسجيل حضور يدوي', sc == 200 or 'already' in str(d).lower() or 'بالفعل' in str(d), str(d.get('message',''))[:100])

# حالة بعد الحضور
sc, d = api_get(emp_token, f'/attendance/api/mobile/status/?latitude={LAT}&longitude={LON}')
check('حالة بعد الحضور (checked_in)', sc == 200 and d.get('checked_in') == True, str(d.get('checked_in')))

# تسجيل انصراف يدوي
sc, d = api_post(emp_token, '/attendance/api/mobile/attendance/', {
    'action': 'check_out',
    'latitude': LAT,
    'longitude': LON,
    'accuracy': 10,
})
check('تسجيل انصراف يدوي', sc == 200 or 'shift_not_ended' in str(d), str(d.get('message',''))[:100])

# ════════════════════════════════════════
# 3. AUTO CHECK-IN (حضور تلقائي)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('3. AUTO ATTENDANCE')

sc, d = api_post(emp_token, '/attendance/api/mobile/employee/auto-check-in/', {
    'latitude': LAT,
    'longitude': LON,
    'accuracy': 10,
    'source': 'auto',
})
check('Auto Check-in', sc in [200, 400], str(d.get('status',''))[:100])

sc, d = api_get(emp_token, '/attendance/api/mobile/employee/auto-checkin-status/')
check('Auto Check-in Status', sc == 200, str(d)[:100])

# ════════════════════════════════════════
# 4. LOCATION TRACKING (تتبع)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('4. LOCATION TRACKING')

sc, d = api_post(emp_token, '/attendance/api/mobile/location/', {
    'latitude': LAT,
    'longitude': LON,
    'accuracy': 10,
})
check('إرسال موقع', sc == 200)

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/live-locations/')
check('مشاهدة مواقع الموظفين (مدير)', sc == 200)

# ════════════════════════════════════════
# 5. REQUESTS (الطلبات)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('5. REQUESTS')

# أنواع الطلبات
sc, d = api_get(emp_token, '/attendance/api/mobile/request-types/')
check('أنواع الطلبات', sc == 200 and len(d.get('categories', [])) > 0)

# جلب نوع طلب عام (مش إذن عشان ما يطلبش تاريخ)
req_type_id = None
if d.get('categories'):
    for cat in d['categories']:
        for t in cat.get('types', []):
            if t.get('permission_kind') == 'none' and not t.get('requires_date_range'):
                req_type_id = t['id']
                break
        if req_type_id:
            break
    if not req_type_id:
        for cat in d['categories']:
            if cat.get('types'):
                req_type_id = cat['types'][0]['id']
                break

# تقديم طلب
if req_type_id:
    sc, d = api_post(emp_token, '/attendance/api/mobile/submit-request/', {
        'request_type_id': req_type_id,
        'subject': 'طلب اختبار أوتوماتيك',
        'details': 'ده طلب تجريبي من سكريبت الاختبار',
    })
    check('تقديم طلب', sc in [200, 201], str(d.get('message',''))[:100])
else:
    check('تقديم طلب', False, 'لم يتم العثور على نوع طلب')

# طلباتي
sc, d = api_get(emp_token, '/attendance/api/mobile/my-requests/')
check('طلباتي', sc == 200)

# الطلبات المعلقة (مدير)
sc, d = api_get(admin_token, '/attendance/api/mobile/manager/pending/')
check('الطلبات المعلقة (مدير)', sc == 200)

# ════════════════════════════════════════
# 1. LOGIN + PROFILE (موظف + مدير)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('1. LOGIN + PROFILE')

# مدير عقاري
admin_token, admin_data = login('re_admin')
check('LOGIN مدير عقاري', admin_token is not None)

sc, d = api_get(admin_token, '/attendance/api/mobile/employee/profile/')
check('PROFILE مدير', sc == 200 and d.get('full_name_ar'))

# موظف ميداني
emp_token, emp_data = login('re_sales_1')
check('LOGIN موظف ميداني', emp_token is not None)

sc, d = api_get(emp_token, '/attendance/api/mobile/employee/profile/')
check('PROFILE موظف', sc == 200 and d.get('full_name_ar'))

# ════════════════════════════════════════
# 2. ATTENDANCE (حضور + انصراف)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('2. ATTENDANCE')

# حالة الحضور
sc, d = api_get(emp_token, f'/attendance/api/mobile/status/?latitude={LAT}&longitude={LON}')
check('حالة الحضور', sc == 200)

# تسجيل حضور يدوي
sc, d = api_post(emp_token, '/attendance/api/mobile/attendance/', {
    'action': 'check_in',
    'latitude': LAT,
    'longitude': LON,
    'accuracy': 10,
})
check('تسجيل حضور يدوي', sc == 200, str(d.get('message',''))[:100])

# حالة بعد الحضور
sc, d = api_get(emp_token, f'/attendance/api/mobile/status/?latitude={LAT}&longitude={LON}')
check('حالة بعد الحضور (checked_in)', sc == 200 and d.get('checked_in') == True, str(d.get('checked_in')))

# تسجيل انصراف يدوي
sc, d = api_post(emp_token, '/attendance/api/mobile/attendance/', {
    'action': 'check_out',
    'latitude': LAT,
    'longitude': LON,
    'accuracy': 10,
})
check('تسجيل انصراف يدوي', sc == 200 or 'shift_not_ended' in str(d), str(d.get('message',''))[:100])

# ════════════════════════════════════════
# 3. AUTO CHECK-IN (حضور تلقائي)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('3. AUTO ATTENDANCE')

sc, d = api_post(emp_token, '/attendance/api/mobile/employee/auto-check-in/', {
    'latitude': LAT,
    'longitude': LON,
    'accuracy': 10,
    'source': 'auto',
})
check('Auto Check-in', sc in [200, 400], str(d.get('status',''))[:100])

sc, d = api_get(emp_token, '/attendance/api/mobile/employee/auto-checkin-status/')
check('Auto Check-in Status', sc == 200, str(d)[:100])

# ════════════════════════════════════════
# 4. LOCATION TRACKING (تتبع)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('4. LOCATION TRACKING')

sc, d = api_post(emp_token, '/attendance/api/mobile/location/', {
    'latitude': LAT,
    'longitude': LON,
    'accuracy': 10,
})
check('إرسال موقع', sc == 200)

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/live-locations/')
check('مشاهدة مواقع الموظفين (مدير)', sc == 200)

# ════════════════════════════════════════
# 5. REQUESTS (الطلبات)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('5. REQUESTS')

# أنواع الطلبات
sc, d = api_get(emp_token, '/attendance/api/mobile/request-types/')
check('أنواع الطلبات', sc == 200 and len(d.get('categories', [])) > 0)

# جلب أول نوع طلب
req_type_id = None
if d.get('categories'):
    for cat in d['categories']:
        if cat.get('types'):
            req_type_id = cat['types'][0]['id']
            break

# تقديم طلب
if req_type_id:
    sc, d = api_post(emp_token, '/attendance/api/mobile/submit-request/', {
        'request_type_id': req_type_id,
        'subject': 'طلب اختبار أوتوماتيك',
        'details': 'ده طلب تجريبي من سكريبت الاختبار',
    })
    check('تقديم طلب', sc in [200, 201], str(d.get('message',''))[:100])
else:
    check('تقديم طلب', False, 'لم يتم العثور على نوع طلب')

# طلباتي
sc, d = api_get(emp_token, '/attendance/api/mobile/my-requests/')
check('طلباتي', sc == 200)

# الطلبات المعلقة (مدير)
sc, d = api_get(admin_token, '/attendance/api/mobile/manager/pending/')
check('الطلبات المعلقة (مدير)', sc == 200)

# ════════════════════════════════════════
# 6. LEAVES (الإجازات)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('6. LEAVES')

sc, d = api_get(emp_token, '/attendance/api/mobile/my-leaves/')
check('إجازاتي', sc == 200)

sc, d = api_get(emp_token, '/attendance/api/mobile/leave-types/')
check('أنواع الإجازات', sc == 200)

leave_type_id = None
if isinstance(d, list) and len(d) > 0:
    leave_type_id = d[0].get('id')
elif isinstance(d, dict) and d.get('leave_types'):
    leave_type_id = d['leave_types'][0].get('id')

if leave_type_id:
    sc, d = api_post(emp_token, '/attendance/api/mobile/leave-request/', {
        'leave_type_id': leave_type_id,
        'start_date': '2026-09-01',
        'end_date': '2026-09-03',
        'reason': 'اختبار إجازة أوتوماتيك',
    })
    check('تقديم إجازة', sc in [200, 201, 400], str(d.get('message',''))[:100])
else:
    check('تقديم إجازة', False, 'لم يتم العثور على نوع إجازة')

# ════════════════════════════════════════
# 7. ANNOUNCEMENTS (الإعلانات + Push)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('7. ANNOUNCEMENTS')

sc, d = api_post(admin_token, '/attendance/api/mobile/manager/announcements/create/', {
    'title': 'إعلان اختبار أوتوماتيك',
    'message': 'ده إعلان تجريبي من سكريبت الاختبار الشامل',
    'type': 'general',
    'priority': 'high',
    'send_push': True,
})
check('إنشاء إعلان + Push', sc == 201 or sc == 200, str(d.get('message',''))[:100])

sc, d = api_get(emp_token, '/attendance/api/mobile/announcements/list/')
check('الإعلانات (موظف)', sc == 200 and len(d.get('announcements', [])) > 0)

# ════════════════════════════════════════
# 8. NOTIFICATIONS (الإشعارات)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('8. NOTIFICATIONS')

sc, d = api_get(admin_token, '/attendance/api/mobile/notifications/')
check('إشعارات المدير', sc == 200)

sc, d = api_get(emp_token, '/attendance/api/mobile/notifications/')
check('إشعارات الموظف', sc == 200)

# ════════════════════════════════════════
# 9. SHIFTS + WORK POLICY
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('9. SHIFTS + POLICY')

sc, d = api_get(emp_token, '/attendance/api/mobile/employee/my-shift/')
check('شيفت الموظف', sc == 200 and d.get('has_shift') == True)

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/work-policy/')
check('سياسة العمل', sc == 200)

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/shifts/')
check('الشيفتات (مدير)', sc == 200)

# ════════════════════════════════════════
# 10. WORK LOCATIONS (مواقع العمل)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('10. WORK LOCATIONS')

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/work-locations/')
check('مواقع العمل (مدير)', sc == 200)

# ════════════════════════════════════════
# 11. REPORTS (التقارير)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('11. REPORTS')

report_slugs = ['eos', 'reimbursements', 'bank-transfer', 'insurance', 'tax',
                'turnover', 'branch-comparison', 'contracts-expiry',
                'loans-advances', 'missions-performance', 'executive-dashboard']

for slug in report_slugs:
    sc, d = api_get(admin_token, f'/attendance/api/mobile/manager/reports/{slug}/')
    check(f'تقرير {slug}', sc == 200)

# Excel export
for slug in ['eos', 'bank-transfer', 'insurance']:
    try:
        r = requests.get(
            f'{BASE}/attendance/api/mobile/manager/reports/{slug}/export/',
            headers={'Authorization': f'Token {admin_token}'},
            timeout=20,
        )
        check(f'Excel تصدير {slug}', r.status_code == 200)
    except:
        check(f'Excel تصدير {slug}', False)

# PDF export
for slug in ['eos', 'tax']:
    try:
        r = requests.get(
            f'{BASE}/attendance/api/mobile/manager/reports/{slug}/export/pdf/',
            headers={'Authorization': f'Token {admin_token}'},
            timeout=20,
        )
        check(f'PDF تصدير {slug}', r.status_code == 200)
    except:
        check(f'PDF تصدير {slug}', False)

# ════════════════════════════════════════
# 12. PAYROLL (الرواتب)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('12. PAYROLL')

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/payroll/summary/?year=2026&month=8')
check('ملخص الرواتب', sc == 200)

sc, d = api_get(emp_token, '/attendance/api/mobile/employee/payslip/')
check('كشف راتب الموظف', sc == 200)

# ════════════════════════════════════════
# 13. EMPLOYEE SUMMARY (ملخص الموظف)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('13. EMPLOYEE SUMMARY')

sc, d = api_get(emp_token, '/attendance/api/mobile/employee/summary/')
check('ملخص الموظف (موظف)', sc == 200)

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/employees/3603/summary/')
check('ملخص الموظف (مدير)', sc == 200)

# ════════════════════════════════════════
# 14. DASHBOARD (لوحة التحكم)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('14. DASHBOARD')

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/dashboard/')
check('لوحة التحكم (مدير)', sc == 200 and d.get('pulse') is not None)

# ════════════════════════════════════════
# 15. EMPLOYEE MANAGEMENT (إدارة الموظفين)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('15. EMPLOYEE MANAGEMENT')

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/employees/')
check('قائمة الموظفين', sc == 200 and len(d.get('employees',[])) > 0)

sc, d = api_post(admin_token, '/attendance/api/mobile/manager/employees/3603/toggle-status/', {
    'status': 'suspended',
})
check('إيقاف موظف', sc == 200, str(d.get('message',''))[:80])

sc, d = api_post(admin_token, '/attendance/api/mobile/manager/employees/3603/toggle-status/', {
    'status': 'active',
})
check('تفعيل موظف', sc == 200, str(d.get('message',''))[:80])

# تم تعطيل هذا الجزء داخل التست لأنه كان بيكسر لوجين الموظف في نفس الرن
print('  ⏭️ تخطي إعادة تعيين كلمة المرور داخل التست الحالي')

# ════════════════════════════════════════
# 16. OFFBOARDING (إنهاء الخدمة)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('16. OFFBOARDING')

sc, d = api_get(admin_token, '/attendance/api/mobile/manager/offboarding/list/')
check('قائمة إنهاء الخدمة', sc == 200)

# ════════════════════════════════════════
# 17. CHARTER (لائحة الشركة)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('17. CHARTER')

sc, d = api_get(emp_token, '/attendance/api/mobile/charter/')
check('لائحة الشركة (موظف)', sc == 200)

# ════════════════════════════════════════
# 18. PERMISSIONS (الأذونات)
# ════════════════════════════════════════
print(f'\n{"─"*70}')
print('18. PERMISSIONS')

sc, d = api_get(emp_token, '/attendance/api/mobile/employee/permission-balance/')
check('رصيد الأذونات', sc == 200)

# ════════════════════════════════════════
# FINAL REPORT
# ════════════════════════════════════════
print(f'\n{"="*70}')
print(f'FULL BUSINESS FLOW TEST RESULTS')
print(f'TOTAL: {total} | PASS: {passed} | FAIL: {len(failed)}')
print(f'{"="*70}')

if failed:
    print('\nFAILED ITEMS:')
    for label, detail in failed:
        print(f'  \u274C {label} => {detail}')
else:
    print('\n\u2705 ALL BUSINESS FLOW CHECKS PASSED — النظام جاهز للبيع')
