"""
سكريبت لإضافة الخطط والميزات الافتراضية
"""

import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()


def seed():
    from subscriptions.models import FeatureFlag, SubscriptionPlan
    
    print("📦 إضافة الميزات...")
    
    features_data = [
        # Core
        ('employees_management', 'إدارة الموظفين', 'Employee Management', 'core', 'bi-people-fill', 1),
        ('companies_management', 'إدارة الشركات', 'Companies Management', 'core', 'bi-building', 2),
        ('branches_management', 'إدارة الفروع', 'Branches Management', 'core', 'bi-shop', 3),
        ('departments_management', 'إدارة الإدارات', 'Departments Management', 'core', 'bi-diagram-3', 4),
        
        # Attendance
        ('attendance_gps', 'حضور بالـ GPS', 'GPS Attendance', 'attendance', 'bi-geo-alt-fill', 10),
        ('attendance_records', 'سجلات الحضور', 'Attendance Records', 'attendance', 'bi-clock-history', 11),
        ('shifts_management', 'إدارة الشيفتات', 'Shifts Management', 'attendance', 'bi-calendar-week', 12),
        
        # Tracking
        ('continuous_tracking', 'التتبع المستمر', 'Continuous Tracking', 'tracking', 'bi-broadcast', 20),
        ('live_map', 'الخريطة الحية', 'Live Map', 'tracking', 'bi-map-fill', 21),
        ('location_visits', 'زيارات المواقع', 'Location Visits', 'tracking', 'bi-pin-map-fill', 22),
        ('field_monitor', 'متابعة الميدانيين', 'Field Monitor', 'tracking', 'bi-people-fill', 23),
        ('geofencing', 'التحقق من النطاق', 'Geofencing', 'tracking', 'bi-shield-check', 24),
        
        # Leaves
        ('leaves_management', 'إدارة الإجازات', 'Leaves Management', 'leaves', 'bi-calendar-check', 30),
        ('leaves_workflow', 'نظام الموافقات', 'Approval Workflow', 'leaves', 'bi-check2-circle', 31),
        ('leave_balances', 'رصيد الإجازات', 'Leave Balances', 'leaves', 'bi-piggy-bank', 32),
        
        # Payroll
        ('payroll_basic', 'المرتبات الأساسية', 'Basic Payroll', 'payroll', 'bi-cash-stack', 40),
        ('payroll_advanced', 'المرتبات المتقدمة', 'Advanced Payroll', 'payroll', 'bi-cash-coin', 41),
        ('insurance', 'التأمينات', 'Insurance', 'payroll', 'bi-shield-fill-check', 42),
        ('taxes', 'الضرائب', 'Taxes', 'payroll', 'bi-receipt', 43),
        ('loans', 'السلف', 'Loans', 'payroll', 'bi-wallet2', 44),
        
        # Reports
        ('basic_reports', 'تقارير أساسية', 'Basic Reports', 'reports', 'bi-file-earmark-text', 50),
        ('advanced_reports', 'تقارير متقدمة', 'Advanced Reports', 'reports', 'bi-graph-up', 51),
        ('export_excel', 'تصدير Excel', 'Excel Export', 'reports', 'bi-file-earmark-excel', 52),
        ('export_pdf', 'تصدير PDF', 'PDF Export', 'reports', 'bi-file-earmark-pdf', 53),
        ('custom_reports', 'تقارير مخصصة', 'Custom Reports', 'reports', 'bi-sliders', 54),
        
        # Recruitment
        ('recruitment', 'التوظيف', 'Recruitment', 'recruitment', 'bi-person-plus-fill', 60),
        ('applicants_tracking', 'متابعة المتقدمين', 'Applicants Tracking', 'recruitment', 'bi-clipboard-check', 61),
        
        # Performance
        ('performance_reviews', 'تقييم الأداء', 'Performance Reviews', 'performance', 'bi-star-fill', 70),
        ('goals_management', 'إدارة الأهداف', 'Goals Management', 'performance', 'bi-bullseye', 71),
        
        # Training
        ('training_management', 'إدارة التدريب', 'Training Management', 'training', 'bi-mortarboard-fill', 80),
        ('certifications', 'الشهادات', 'Certifications', 'training', 'bi-award-fill', 81),
        
        # Advanced
        ('multi_branch', 'متعدد الفروع', 'Multi-branch', 'advanced', 'bi-diagram-2', 90),
        ('white_label', 'White Label', 'White Label', 'advanced', 'bi-palette-fill', 91),
        ('api_access', 'API Access', 'API Access', 'advanced', 'bi-code-slash', 92),
        ('custom_domain', 'Domain مخصص', 'Custom Domain', 'advanced', 'bi-globe', 93),
        ('priority_support', 'دعم مميز', 'Priority Support', 'advanced', 'bi-headset', 94),
    ]
    
    for key, name_ar, name_en, category, icon, order in features_data:
        feature, created = FeatureFlag.objects.get_or_create(
            key=key,
            defaults={
                'name_ar': name_ar,
                'name_en': name_en,
                'category': category,
                'icon': icon,
                'order': order,
            }
        )
        if created:
            print(f"  ✅ {name_ar}")
    
    print()
    print("📦 إضافة الخطط...")
    
    # Trial Plan
    trial_plan, _ = SubscriptionPlan.objects.get_or_create(
        tier='trial',
        defaults={
            'name_ar': 'تجربة مجانية',
            'name_en': 'Free Trial',
            'description': 'تجربة كل ميزات النظام مجاناً',
            'price_monthly': 0,
            'price_yearly': 0,
            'max_employees': 10,
            'max_branches': 1,
            'max_departments': 5,
            'is_trial': True,
            'trial_days': 14,
            'color': '#8B5CF6',
            'is_featured': False,
            'order': 0,
        }
    )
    # Trial: كل الميزات
    trial_plan.features.set(FeatureFlag.objects.all())
    print(f"  ✅ {trial_plan.name_ar}")
    
    # Starter Plan
    starter, _ = SubscriptionPlan.objects.get_or_create(
        tier='starter',
        defaults={
            'name_ar': 'Starter',
            'name_en': 'Starter',
            'description': 'مثالية للشركات الصغيرة',
            'price_monthly': 299,
            'price_yearly': 2999,
            'max_employees': 15,
            'max_branches': 1,
            'max_departments': 5,
            'color': '#10B981',
            'order': 1,
        }
    )
    starter_features = [
        'employees_management', 'companies_management', 'branches_management',
        'departments_management', 'attendance_gps', 'attendance_records',
        'basic_reports', 'export_excel'
    ]
    starter.features.set(FeatureFlag.objects.filter(key__in=starter_features))
    print(f"  ✅ {starter.name_ar}")
    
    # Business Plan
    business, _ = SubscriptionPlan.objects.get_or_create(
        tier='business',
        defaults={
            'name_ar': 'Business',
            'name_en': 'Business',
            'description': 'للشركات المتوسطة',
            'price_monthly': 599,
            'price_yearly': 5999,
            'max_employees': 50,
            'max_branches': 3,
            'max_departments': 10,
            'color': '#06B6D4',
            'is_featured': True,
            'order': 2,
        }
    )
    business_features = starter_features + [
        'shifts_management', 'continuous_tracking', 'live_map',
        'location_visits', 'field_monitor', 'geofencing',
        'leaves_management', 'leaves_workflow', 'leave_balances',
        'export_pdf'
    ]
    business.features.set(FeatureFlag.objects.filter(key__in=business_features))
    print(f"  ✅ {business.name_ar}")
    
    # Professional Plan
    professional, _ = SubscriptionPlan.objects.get_or_create(
        tier='professional',
        defaults={
            'name_ar': 'Professional',
            'name_en': 'Professional',
            'description': 'للشركات الكبيرة',
            'price_monthly': 999,
            'price_yearly': 9999,
            'max_employees': 100,
            'max_branches': 10,
            'max_departments': 30,
            'color': '#3B82F6',
            'order': 3,
        }
    )
    professional_features = business_features + [
        'payroll_basic', 'insurance', 'taxes', 'loans',
        'advanced_reports', 'custom_reports', 'multi_branch'
    ]
    professional.features.set(FeatureFlag.objects.filter(key__in=professional_features))
    print(f"  ✅ {professional.name_ar}")
    
    # Enterprise Plan
    enterprise, _ = SubscriptionPlan.objects.get_or_create(
        tier='enterprise',
        defaults={
            'name_ar': 'Enterprise',
            'name_en': 'Enterprise',
            'description': 'حلول شاملة للمؤسسات الكبيرة',
            'price_monthly': 2000,
            'price_yearly': 20000,
            'max_employees': 0,  # غير محدود
            'max_branches': 0,
            'max_departments': 0,
            'color': '#F59E0B',
            'order': 4,
        }
    )
    # Enterprise: كل الميزات
    enterprise.features.set(FeatureFlag.objects.all())
    print(f"  ✅ {enterprise.name_ar}")
    
    print()
    print("=" * 60)
    print(f"📊 إجمالي الميزات: {FeatureFlag.objects.count()}")
    print(f"📊 إجمالي الخطط: {SubscriptionPlan.objects.count()}")
    print("=" * 60)


if __name__ == '__main__':
    seed()
