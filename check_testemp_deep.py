import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from django.contrib.auth import get_user_model
from employees.models import Employee
from attendance.models import Attendance, Shift
from attendance.api_mobile import get_active_shift, get_shift_bounds, get_shift_periods
from django.utils import timezone
from django.db.models import Q

User = get_user_model()

print('='*70)
print('🔍 [فحص شامل لليوزرات الاختبارية في قاعدة البيانات المباشرة]')

users = User.objects.filter(
    Q(username__icontains='testemp') | 
    Q(username__icontains='mwzf') | 
    Q(first_name__icontains='تجريبي') | 
    Q(first_name__icontains='اختباري')
)

print(f'عدد اليوزرات المكتشفة المطابقة: {users.count()}')

for u in users:
    print(f'\n👤 اليوزر: {u.username} (اسم: {u.get_full_name() or "بدون"}) | ID={u.id}')
    if hasattr(u, 'employee') and u.employee:
        emp = u.employee
        today = timezone.localdate()
        now = timezone.now()
        
        att = Attendance._base_manager.filter(employee=emp).order_by('-id').first()
        if att:
            print(f'   📊 آخر سجل حضور: ID={att.id} | التاريخ={att.date} | حضور={att.check_in_time} | انصراف={att.check_out_time}')
        else:
            print('   📊 لا يوجد سجل حضور سابق!')
            
        shift = get_active_shift(emp, att.date if att else today)
        print(f'   ⚙️ الشيفت المكتشف: {shift}')
        if shift:
            print(f'      - بداية: {shift.start_time} | نهاية: {shift.end_time}')
            print(f'      - crosses_midnight: {getattr(shift, "crosses_midnight", False)}')
            print(f'      - shift_mode: {getattr(shift, "shift_mode", "fixed")}')
            
            s_start, s_end = get_shift_bounds(shift, att.date if att else today)
            print(f'      - s_start المحسوب: {s_start}')
            print(f'      - s_end المحسوب: {s_end}')
            
            if s_end:
                diff_secs = (s_end - now).total_seconds()
                hours = int(diff_secs // 3600)
                mins = int((diff_secs % 3600) // 60)
                print(f'      - [الفرق الحسابي المباشر الان]: {diff_secs:.1f} ثانية')
                print(f'      - [الرسالة المتوقعة للموبايل]: فاضل {hours} ساعة و {mins} دقيقة')
print('='*70)
