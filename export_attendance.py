import csv
from pathlib import Path
from datetime import date
from django.utils import timezone
from employees.models import Employee
from attendance.models import Attendance

# اتركهما None لتضمين كل السجل، أو حدّد فترة مثل date(2026, 1, 1)
START_DATE = None
END_DATE = None

employees = Employee._base_manager.filter(
    first_name_ar__iexact="إيهاب",
    middle_name_ar__iexact="زينهم",
    last_name_ar__iexact="سيد",
)

if employees.count() != 1:
    raise ValueError(
        f"المفروض نلاقي موظفًا واحدًا بالاسم ده؛ الموجود: {employees.count()}"
    )

employee = employees.get()

attendance_rows = Attendance._base_manager.filter(
    employee=employee
).select_related("shift").prefetch_related("sessions").order_by("date")

if START_DATE:
    attendance_rows = attendance_rows.filter(date__gte=START_DATE)
if END_DATE:
    attendance_rows = attendance_rows.filter(date__lte=END_DATE)

def format_datetime(value):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%Y-%m-%d %H:%M:%S")

def map_link(latitude, longitude):
    if latitude is None or longitude is None:
        return ""
    return f"https://www.google.com/maps?q={latitude},{longitude}"

output = Path.cwd() / "attendance_ehab_zainhom_sayed.csv"
rows_written = 0

with output.open("w", newline="", encoding="utf-8-sig") as csvfile:
    report = csv.writer(csvfile)
    report.writerow([
        "التاريخ", "رقم الفترة", "الحالة", "الشيفت",
        "وقت الحضور", "عنوان الحضور", "خط عرض الحضور",
        "خط طول الحضور", "خريطة الحضور",
        "وقت الانصراف", "عنوان الانصراف", "خط عرض الانصراف",
        "خط طول الانصراف", "خريطة الانصراف",
        "ساعات العمل", "دقائق التأخير", "دقائق الانصراف المبكر",
    ])

    for attendance in attendance_rows:
        sessions = list(attendance.sessions.all())
        periods = sessions or [None]

        for index, session in enumerate(periods):
            first_period = index == 0
            last_period = index == len(periods) - 1

            if session is None:
                check_in = attendance.check_in_time
                check_out = attendance.check_out_time
                in_lat = attendance.check_in_latitude
                in_lon = attendance.check_in_longitude
                out_lat = attendance.check_out_latitude
                out_lon = attendance.check_out_longitude
                in_address = attendance.check_in_address or ""
                out_address = attendance.check_out_address or ""
                hours = attendance.work_hours or 0
                period_number = ""
            else:
                check_in = session.check_in_time
                check_out = session.check_out_time

                in_lat = session.check_in_latitude
                in_lon = session.check_in_longitude
                out_lat = session.check_out_latitude
                out_lon = session.check_out_longitude

                # العناوين محفوظة في سجل اليوم؛ اعرضها مع أول/آخر فترة فقط.
                in_address = (
                    (attendance.check_in_address or "")
                    if first_period else ""
                )
                out_address = (
                    (attendance.check_out_address or "")
                    if last_period else ""
                )

                # لو إحداثيات الفترة مش موجودة، استخدم إحداثيات سجل اليوم لأول/آخر فترة.
                if first_period:
                    if in_lat is None:
                        in_lat = attendance.check_in_latitude
                    if in_lon is None:
                        in_lon = attendance.check_in_longitude
                if last_period:
                    if out_lat is None:
                        out_lat = attendance.check_out_latitude
                    if out_lon is None:
                        out_lon = attendance.check_out_longitude

                minutes = session.worked_minutes or 0
                if not minutes and check_in and check_out:
                    minutes = int((check_out - check_in).total_seconds() / 60)
                hours = round(minutes / 60, 2)
                period_number = session.session_number

            report.writerow([
                attendance.date.isoformat(),
                period_number,
                attendance.get_status_display(),
                attendance.shift.name if attendance.shift_id else "",
                format_datetime(check_in),
                in_address,
                in_lat if in_lat is not None else "",
                in_lon if in_lon is not None else "",
                map_link(in_lat, in_lon),
                format_datetime(check_out),
                out_address,
                out_lat if out_lat is not None else "",
                out_lon if out_lon is not None else "",
                map_link(out_lat, out_lon),
                hours,
                attendance.late_minutes,
                attendance.early_leave_minutes,
            ])
            rows_written += 1

print(f"تم إنشاء التقرير: {output}")
print(f"عدد الصفوف: {rows_written}")
