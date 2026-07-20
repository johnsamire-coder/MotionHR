"""
Management Command: seed_request_types
يزرع فئات وأنواع الطلبات لكل شركة موجودة
آمن تمامًا - يستخدم get_or_create فلا يكرر البيانات
"""
from django.core.management.base import BaseCommand
from companies.models import Company
from requests_app.models import RequestCategory, RequestType


SEED_DATA = [
    {
        "name": "إجازات",
        "name_en": "Leaves",
        "icon": "bi-calendar-check",
        "color": "#10B981",
        "order": 1,
        "types": [
            {
                "name": "إجازة سنوية",
                "name_en": "Annual Leave",
                "requires_date_range": True,
                "requires_amount": False,
                "requires_document": False,
                "permission_kind": "none",
                "order": 1,
            },
            {
                "name": "إجازة مرضية",
                "name_en": "Sick Leave",
                "requires_date_range": True,
                "requires_amount": False,
                "requires_document": True,
                "permission_kind": "none",
                "order": 2,
            },
            {
                "name": "إجازة طارئة",
                "name_en": "Emergency Leave",
                "requires_date_range": True,
                "requires_amount": False,
                "requires_document": False,
                "permission_kind": "none",
                "order": 3,
            },
            {
                "name": "إجازة بدون أجر",
                "name_en": "Unpaid Leave",
                "requires_date_range": True,
                "requires_amount": False,
                "requires_document": False,
                "permission_kind": "none",
                "order": 4,
            },
        ],
    },
    {
        "name": "أذونات الحضور",
        "name_en": "Attendance Permissions",
        "icon": "bi-clock",
        "color": "#F59E0B",
        "order": 2,
        "types": [
            {
                "name": "إذن تأخير",
                "name_en": "Late Arrival",
                "requires_date_range": False,
                "requires_amount": False,
                "requires_document": False,
                "permission_kind": "late_arrival",
                "order": 1,
            },
            {
                "name": "إذن خروج مبكر",
                "name_en": "Early Leave",
                "requires_date_range": False,
                "requires_amount": False,
                "requires_document": False,
                "permission_kind": "early_leave",
                "order": 2,
            },
        ],
    },
    {
        "name": "الرواتب والمكافآت",
        "name_en": "Payroll & Bonuses",
        "icon": "bi-cash-coin",
        "color": "#6366F1",
        "order": 3,
        "types": [
            {
                "name": "سلفة",
                "name_en": "Advance Salary",
                "requires_date_range": False,
                "requires_amount": True,
                "requires_document": False,
                "permission_kind": "none",
                "order": 1,
            },
            {
                "name": "طلب مكافأة",
                "name_en": "Bonus Request",
                "requires_date_range": False,
                "requires_amount": True,
                "requires_document": False,
                "permission_kind": "none",
                "order": 2,
            },
        ],
    },
    {
        "name": "طلبات إدارية",
        "name_en": "Administrative Requests",
        "icon": "bi-file-text",
        "color": "#06B6D4",
        "order": 4,
        "types": [
            {
                "name": "خطاب رسمي",
                "name_en": "Official Letter",
                "requires_date_range": False,
                "requires_amount": False,
                "requires_document": False,
                "permission_kind": "none",
                "order": 1,
            },
            {
                "name": "شهادة راتب",
                "name_en": "Salary Certificate",
                "requires_date_range": False,
                "requires_amount": False,
                "requires_document": False,
                "permission_kind": "none",
                "order": 2,
            },
            {
                "name": "تعديل بيانات",
                "name_en": "Data Update",
                "requires_date_range": False,
                "requires_amount": False,
                "requires_document": True,
                "permission_kind": "none",
                "order": 3,
            },
        ],
    },
    {
        "name": "أخرى",
        "name_en": "Other",
        "icon": "bi-three-dots",
        "color": "#64748B",
        "order": 5,
        "types": [
            {
                "name": "طلب آخر",
                "name_en": "Other Request",
                "requires_date_range": False,
                "requires_amount": False,
                "requires_document": False,
                "permission_kind": "none",
                "order": 1,
            },
        ],
    },
]


def seed_for_company(company, verbosity=1):
    created_cats = 0
    created_types = 0

    for cat_data in SEED_DATA:
        types_data = cat_data.pop("types")
        cat, cat_created = RequestCategory.all_objects.get_or_create(
            company=company,
            name=cat_data["name"],
            defaults=cat_data,
        )
        if cat_created:
            created_cats += 1
            if verbosity >= 1:
                print(f"  ✅ فئة جديدة: {cat.name}")
        # restore
        cat_data["types"] = types_data

        for type_data in types_data:
            t, t_created = RequestType.all_objects.get_or_create(
                company=company,
                category=cat,
                name=type_data["name"],
                defaults=type_data,
            )
            if t_created:
                created_types += 1
                if verbosity >= 1:
                    print(f"    ✅ نوع جديد: {t.name}")

    return created_cats, created_types


class Command(BaseCommand):
    help = "يزرع فئات وأنواع الطلبات لكل الشركات"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company-id",
            type=int,
            help="زرع لشركة معينة فقط",
        )

    def handle(self, *args, **options):
        company_id = options.get("company_id")
        if company_id:
            companies = Company.objects.filter(pk=company_id)
        else:
            companies = Company.objects.filter(is_active=True)

        total_cats = 0
        total_types = 0

        for company in companies:
            self.stdout.write(f"\n🏢 شركة: {company.name_ar} (id={company.id})")
            cats, types = seed_for_company(company, verbosity=options.get("verbosity", 1))
            total_cats += cats
            total_types += types

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ انتهى: {total_cats} فئة + {total_types} نوع تم إنشاؤهم"
            )
        )
