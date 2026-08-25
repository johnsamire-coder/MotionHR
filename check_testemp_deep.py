import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from django.contrib.auth import get_user_model
from employees.models import Employee
from attendance.models import Attendance, Shift
from attendance.api_mobile import get_active_shift, get_shift_bounds
from django.utils import timezone

print('='*70)
print('🔍 [فحص عميق وشامل لبيانات وشيفت الموظف testemp]')

emp = Employee._base_manager.filter(user__username__icontains='testemp').first()
if not emp:
    emp = Employee._base_manager.filter(first_name__icontains='تجريبي').first()

if not emp:
    print('❌ لم نجد الموظف المربوط باليوزر testemp بشكل مباشر!')
    print('قائمة الموظفين الأوائل في النظام:')
    for e in Employee._base_manager.all()[:10]:
        uname = e.user.username if e.user else 'بدون يوزر'
        print(f' - ID: {e.id}, User: {uname}, Name: {e.get_full_name()}')
else:
    u = emp.user
    today = timezone.localdate()
    now = timezone.now()
    
    print(f'✅ تم العثور على الموظف: ID={emp.id} | Name={emp.get_full_name()} | User={u.username if u else "None"}')
    print(f'🏢 الشركة: {emp.company.name if emp.company else "بدون"} (ID={emp.company_id})')
    print(f'📅 اليوم المحلي بالسيرفر: {today} | الوقت الحالي (now): {now}')
    
    att = Attendance._base_manager.filter(employee=emp).order_by('-id').first()
    if att:
        print(f'📊 آخر سجل حضور:')
        print(f'   - ID السجل: {att.id}')
        print(f'   - تاريخ السجل (att.date): {att.date}')
        print(f'   - check_in_time: {att.check_in_time}')
        print(f'   - check_out_time: {att.check_out_time}')
    else:
        print('📊 لا يوجد أي سجل حضور لهذا الموظف!')
        
    att_date = att.date if (att and att.date) else today
    shift = get_active_shift(emp, att_date)
    print(f'⚙️ الشيفت المكتشف لـ {att_date}: {shift}')
    
    if shift:
        print(f'   - ID الشيفت: {shift.id}')
        print(f'   - اسم الشيفت: {shift.name}')
        print(f'   - start_time: {shift.start_time}')
        print(f'   - end_time: {shift.end_time}')
        print(f'   - crosses_midnight: {getattr(shift, "crosses_midnight", False)}')
        print(f'   - shift_mode: {getattr(shift, "shift_mode", "fixed")}')
        
        s_start, s_end = get_shift_bounds(shift, att_date)
        print(f'   - s_start (get_shift_bounds): {s_start}')
        print(f'   - s_end (get_shift_bounds): {s_end}')
        
        if s_end:
            diff_secs = (s_end - now).total_seconds()
            print(f'   - (s_end - now) بالثواني: {diff_secs:.1f}')
            print(f'   - الساعات المتبقية: {round(diff_secs / 3600.0, 2)} ساعة')
            h = int(diff_secs // 3600)
            m = int((diff_secs % 3600) // 60)
            print(f'   - [النتيجة المعروضة للموبايل]: فاضل {h} ساعة و {m} دقيقة')
print('='*70)
