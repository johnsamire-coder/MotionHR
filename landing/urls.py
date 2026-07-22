from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.smart_home, name='home'),

    # صفحة "قريباً" (لتحميل التطبيق أو الفيديو)
    path('coming-soon/', views.coming_soon, name='coming_soon'),

    # صفحات أخرى
    path('about/', views.landing_about, name='about'),
    path('contact/', views.landing_contact, name='contact'),

    # التجربة المجانية / طلب عرض سعر
    path('free-trial/', views.free_trial_register, name='free_trial'),
    path('free-trial/success/', views.free_trial_success, name='free_trial_success'),

    # JS Solutions
    path('js-solutions/', views.js_solutions_home, name='js_solutions'),

    # ═══════════════════════════════════════════
    # الأسعار: مؤجلة (سنستخدم عرض سعر مخصص)
    # ═══════════════════════════════════════════
    # path('pricing/', views.landing_pricing, name='pricing'),
]