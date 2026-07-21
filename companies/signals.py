"""
Companies Signals
Auto-create default templates لأي شركة جديدة
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from companies.models import Company


@receiver(post_save, sender=Company)
def create_default_templates_for_new_company(sender, instance, created, **kwargs):
    """
    Signal handler
    يشتغل تلقائياً بعد ما شركة جديدة تُنشأ (post_save)
    ينسخ كل الـ Templates الافتراضية للشركة
    """
    # نشتغل بس لو الشركة جديدة (created=True)
    if not created:
        return

    # نتجاهل شركات الاختبار (اللي بتبدأ بـ __TEST_)
    company_name = instance.name_ar or instance.name_en or ''
    if company_name.startswith('__TEST_'):
        return

    # نأجل التشغيل لبعد انتهاء الـ transaction الحالية
    # (عشان نتأكد إن الشركة اتحفظت فعلاً)
    transaction.on_commit(lambda: _run_seeder(instance))


def _run_seeder(company):
    """
    تشغيل الـ Seeder فعلياً
    محاطة بـ try/except عشان لو حصل خطأ، الشركة تفضل موجودة
    """
    try:
        from core.company_templates.seeder import seed_company_defaults

        stats = seed_company_defaults(company, user=None)

        # لو فيه errors، نطبعها في اللوج (بس مش نوقف الشركة)
        if stats.get('errors'):
            print(f"⚠️  Company '{company}' - Seeder warnings:")
            for err in stats['errors']:
                print(f"   - {err}")
        else:
            print(f"✅ Company '{company}' - Seeder completed:")
            print(f"   Job Titles: {stats['job_titles']}")
            print(f"   Leave Types: {stats['leave_types']}")
            print(f"   Categories: {stats['request_categories']}")
            print(f"   Request Types: {stats['request_types']}")

    except Exception as e:
        # لو حصل أي خطأ، نطبعه بس مش نوقف الـ flow
        print(f"❌ Company '{company}' - Seeder failed: {str(e)}")
        import traceback
        traceback.print_exc()
