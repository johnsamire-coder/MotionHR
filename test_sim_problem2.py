from datetime import datetime, time, timedelta
from django.utils import timezone

# محاكاة منطق get_shift_bounds المصحح لليوزر Testemp
today = datetime.now().date()
start_time = time(18, 30) # 6:30 PM
end_time = time(23, 0)   # 11:00 PM

start_dt = datetime.combine(today, start_time)
end_dt = datetime.combine(today, end_time)

# الموظف سجل حضور 18:34 والآن الساعة 18:35 مثلاً
now_dt = datetime.combine(today, time(18, 35))

diff_secs = (end_dt - now_dt).total_seconds()
hours = int(diff_secs // 3600)
mins = int((diff_secs % 3600) // 60)

print('='*50)
print('🧪 [نتيجة محاكاة الانصراف لـ Testemp بعد الإصلاح]:')
print(f'- وقت الشيفت: {start_time.strftime("%H:%M")} إلى {end_time.strftime("%H:%M")}')
print(f'- الوقت عند الانصراف: {now_dt.strftime("%H:%M")}')
print(f'- الوقت المتبقي المحسوب بدقة: {hours} ساعة و {mins} دقيقة')
print(f'- النتيجة: {"نجاح ✅ (الوقت المتبقي أقل من 4.5 ساعات)" if hours < 5 else "خطأ ❌"}')
print('='*50)
