"""
Company Templates Seeder
الفنكشن دي بتنشئ كل الـ Templates الافتراضية لأي شركة جديدة
- Job Titles
- Leave Types
- Request Categories + Request Types

يتم استدعاؤها تلقائياً عن طريق Signal لما شركة جديدة تُنشأ
أو يدوياً من الـ Admin عند الحاجة
"""

from django.db import transaction


def seed_company_defaults(company, user=None):
    """
    ينشئ كل الـ defaults للشركة الجديدة
    
    Args:
        company: Company instance (الشركة اللي هننشئ لها البيانات)
        user: User اللي بيعمل الإنشاء (اختياري - لحفظ created_by)
    
    Returns:
        dict: إحصائيات إيه اللي اتنشئ
    """
    from .job_titles import DEFAULT_JOB_TITLES
    from .leave_types import DEFAULT_LEAVE_TYPES
    from .request_categories import DEFAULT_REQUEST_CATEGORIES
    from .request_types import DEFAULT_REQUEST_TYPES

    stats = {
        'job_titles': 0,
        'leave_types': 0,
        'request_categories': 0,
        'request_types': 0,
        'errors': [],
    }

    try:
        with transaction.atomic():
            # ═══════════════════════════════════════════════════
            # 1. Job Titles
            # ═══════════════════════════════════════════════════
            stats['job_titles'] = _seed_job_titles(
                company, user, DEFAULT_JOB_TITLES, stats
            )

            # ═══════════════════════════════════════════════════
            # 2. Leave Types
            # ═══════════════════════════════════════════════════
            stats['leave_types'] = _seed_leave_types(
                company, user, DEFAULT_LEAVE_TYPES, stats
            )

            # ═══════════════════════════════════════════════════
            # 3. Request Categories
            # ═══════════════════════════════════════════════════
            categories_map = _seed_request_categories(
                company, user, DEFAULT_REQUEST_CATEGORIES, stats
            )

            # ═══════════════════════════════════════════════════
            # 4. Request Types (تعتمد على Categories)
            # ═══════════════════════════════════════════════════
            stats['request_types'] = _seed_request_types(
                company, user, DEFAULT_REQUEST_TYPES, categories_map, stats
            )

    except Exception as e:
        stats['errors'].append(f"General error: {str(e)}")

    return stats


def _seed_job_titles(company, user, defaults, stats):
    """إنشاء المسميات الوظيفية"""
    from employees.models import JobTitle
    count = 0

    for item in defaults:
        try:
            # نتأكد إنها مش موجودة (لمنع التكرار)
            exists = JobTitle._base_manager.filter(
                company=company,
                name_ar=item['name_ar']
            ).exists()

            if not exists:
                job_title = JobTitle(
                    company=company,
                    name_ar=item['name_ar'],
                    name_en=item['name_en'],
                )
                if user:
                    job_title.created_by = user
                    job_title.updated_by = user
                job_title.save()
                count += 1
        except Exception as e:
            stats['errors'].append(f"JobTitle '{item['name_ar']}': {str(e)}")

    return count


def _seed_leave_types(company, user, defaults, stats):
    """إنشاء أنواع الإجازات"""
    from leaves.models import LeaveType
    count = 0

    for item in defaults:
        try:
            exists = LeaveType._base_manager.filter(
                company=company,
                name=item['name']
            ).exists()

            if not exists:
                leave_type = LeaveType(
                    company=company,
                    name=item['name'],
                    category=item['category'],
                    days_allowed=item['days_allowed'],
                    is_paid=item['is_paid'],
                    requires_approval=item['requires_approval'],
                    requires_document=item['requires_document'],
                    carry_forward=item['carry_forward'],
                    max_carry_days=item['max_carry_days'],
                    color=item['color'],
                    description=item.get('description', ''),
                    is_active=item['is_active'],
                )
                if user:
                    leave_type.created_by = user
                    leave_type.updated_by = user
                leave_type.save()
                count += 1
        except Exception as e:
            stats['errors'].append(f"LeaveType '{item['name']}': {str(e)}")

    return count


def _seed_request_categories(company, user, defaults, stats):
    """
    إنشاء فئات الطلبات
    Returns: dict مربوط اسم الفئة بـ instance بتاعها
             (هنستخدمها في إنشاء Request Types)
    """
    from requests_app.models import RequestCategory
    categories_map = {}

    for item in defaults:
        try:
            # نتأكد لو موجودة
            category = RequestCategory._base_manager.filter(
                company=company,
                name=item['name']
            ).first()

            if not category:
                category = RequestCategory(
                    company=company,
                    name=item['name'],
                    name_en=item['name_en'],
                    icon=item['icon'],
                    color=item['color'],
                    order=item['order'],
                    is_active=item['is_active'],
                )
                if user:
                    category.created_by = user
                    category.updated_by = user
                category.save()
                stats['request_categories'] += 1

            # نحفظها في الـ map عشان نستخدمها بعدين
            categories_map[item['name']] = category

        except Exception as e:
            stats['errors'].append(f"RequestCategory '{item['name']}': {str(e)}")

    return categories_map


def _seed_request_types(company, user, defaults, categories_map, stats):
    """إنشاء أنواع الطلبات (مربوطة بالفئات)"""
    from requests_app.models import RequestType
    count = 0

    for item in defaults:
        try:
            # نجيب الفئة المربوطة
            category = categories_map.get(item['category_key'])
            if not category:
                stats['errors'].append(
                    f"RequestType '{item['name']}': "
                    f"Category '{item['category_key']}' not found"
                )
                continue

            exists = RequestType._base_manager.filter(
                company=company,
                name=item['name']
            ).exists()

            if not exists:
                request_type = RequestType(
                    company=company,
                    category=category,
                    name=item['name'],
                    name_en=item['name_en'],
                    description=item.get('description', ''),
                    description_en=item.get('description_en', ''),
                    requires_date_range=item['requires_date_range'],
                    requires_amount=item['requires_amount'],
                    requires_document=item['requires_document'],
                    requires_approval=item['requires_approval'],
                    permission_kind=item.get('permission_kind'),
                    order=item['order'],
                    is_active=item['is_active'],
                )
                if user:
                    request_type.created_by = user
                    request_type.updated_by = user
                request_type.save()
                count += 1
        except Exception as e:
            stats['errors'].append(f"RequestType '{item['name']}': {str(e)}")

    return count
