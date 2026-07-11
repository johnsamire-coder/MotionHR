# دليل Simulation الكامل لـ MotionHR

## تشغيل السيرفر
```bash
.venv\\Scripts\\activate
python manage.py runserver 0.0.0.0:8000
```

## سيناريو الـ Simulation

### المرحلة 1: Landing Page
- [ ] افتح / - Landing Page
- [ ] /pricing/ - الاسعار
- [ ] /about/ - عن النظام
- [ ] /contact/ - تواصل معنا

### المرحلة 2: تسجيل الدخول
- [ ] /login/ - سجل دخول
- [ ] تأكد redirect لـ /dashboard/

### المرحلة 3: Admin Setup
- [ ] /admin/ - انشئ Company
- [ ] انشئ Subscription
- [ ] انشئ Branch بـ GPS
- [ ] انشئ Department + Shift

### المرحلة 4: Dashboard
- [ ] /dashboard/ - ارقام حقيقية

### المرحلة 5: الموظفين
- [ ] /employees/add/ - اضف موظف
- [ ] انشئ حساب من تبويب الحساب

### المرحلة 6: الحضور
- [ ] /attendance/check-in/ - سجل حضور
- [ ] /attendance/map/ - الخريطة

### المرحلة 7: الاجازات
- [ ] /leaves/types/ - اضف نوع
- [ ] /leaves/add/ - قدم طلب
- [ ] وافق على الطلب

### المرحلة 8: التقارير
- [ ] /reports/ - جرب كل التقارير
- [ ] Export Excel

### المرحلة 9: الاشتراكات
- [ ] /subscriptions/my-plan/
- [ ] /subscriptions/contact-sales/

### المرحلة 10: الملف الشخصي
- [ ] /accounts/profile/
- [ ] /accounts/notifications/

### المرحلة 11: البحث
- [ ] /search/?q=اسم

### المرحلة 12: PWA
- [ ] http://192.168.1.45:8000 من الموبايل
- [ ] Banner التثبيت
- [ ] /offline/

### المرحلة 13: الاخطاء
- [ ] /xxxxx/ - 404 مخصص

## امر انشاء بيانات تجريبية
```bash
python manage.py shell
```
```python
from companies.models import Company, Branch
from accounts.models import User

company = Company.objects.create(
    name_ar='شركة الاختبار',
    email='test@company.com',
    phone='01000000000',
)

branch = Branch.objects.create(
    company=company,
    name_ar='المقر الرئيسي',
    latitude=30.0444,
    longitude=31.2357,
    check_in_radius=200,
    is_main=True,
)

print('Done!')
exit()
```

## ملخص النظام

| الوحدة | الحالة |
|--------|--------|
| Landing Page | مكتمل |
| Auth | مكتمل |
| Dashboard | مكتمل |
| Employees | مكتمل |
| Attendance GPS | مكتمل |
| Companies | مكتمل |
| Leaves | مكتمل |
| Reports | مكتمل |
| Subscriptions | مكتمل |
| PWA | مكتمل |
| Profile | مكتمل |
| Search | مكتمل |
| 404/500 | مكتمل |