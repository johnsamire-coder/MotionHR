# MotionHR — Production Deployment Checklist

## ما الذي ستشتريه؟
1. دومين
2. VPS Ubuntu 22.04

## أقل مواصفات مناسبة:
- 2 vCPU
- 2 GB RAM
- 50 GB SSD
- Ubuntu 22.04

## البيانات التي أحتاجها منك بعد الشراء:
1. IP السيرفر
2. اسم الدومين
3. اسم المستخدم للدخول (غالبًا root)
4. كلمة المرور أو SSH access

## التسلسل:
1. شراء الدومين
2. شراء VPS
3. ربط الدومين بالـ IP
4. رفع المشروع
5. إعداد PostgreSQL
6. إعداد Gunicorn
7. إعداد Nginx
8. تفعيل SSL
9. اختبار:
   - /
   - /pricing/
   - /free-trial/
   - /accounts/login/
