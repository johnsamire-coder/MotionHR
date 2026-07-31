"""
MotionHR - Official Holidays (الإجازات الرسمية)
"""
from django.db import models
from django.conf import settings
from core.models import TenantModel


class OfficialHoliday(TenantModel):
    """إجازة رسمية أساسية"""

    name = models.CharField(max_length=200, verbose_name="اسم الإجازة")
    start_date = models.DateField(verbose_name="من تاريخ")
    end_date = models.DateField(verbose_name="إلى تاريخ")
    notes = models.TextField(blank=True, default="", verbose_name="ملاحظات")
    is_active = models.BooleanField(default=True, verbose_name="نشطة")
    send_notification = models.BooleanField(default=True, verbose_name="إرسال إشعار")
    remind_day_before = models.BooleanField(default=False, verbose_name="تذكير قبل بيوم")

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "إجازة رسمية"
        verbose_name_plural = "الإجازات الرسمية"

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date})"

    @property
    def days_count(self):
        return (self.end_date - self.start_date).days + 1


class OfficialHolidayRule(TenantModel):
    """قاعدة معاملة لفئة معينة داخل الإجازة الرسمية"""

    SCOPE_CHOICES = [
        ("company", "الشركة كلها"),
        ("branch", "فرع محدد"),
        ("department", "قسم محدد"),
        ("employees", "موظفين محددين"),
    ]

    TREATMENT_CHOICES = [
        ("paid_leave", "إجازة مدفوعة"),
        ("work_with_bonus", "عمل بمقابل إضافي"),
        ("normal_work", "يوم عمل عادي"),
    ]

    BONUS_CALC_CHOICES = [
        ("fixed_amount", "مبلغ ثابت"),
        ("salary_percentage", "نسبة من المرتب الأساسي"),
        ("day_multiplier", "مضاعف أجر اليوم"),
    ]

    holiday = models.ForeignKey(
        OfficialHoliday,
        on_delete=models.CASCADE,
        related_name="rules",
        verbose_name="الإجازة الرسمية",
    )

    # النطاق
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default="company",
        verbose_name="يتطبق على",
    )
    branch = models.ForeignKey(
        "companies.Branch",
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="الفرع",
    )
    department = models.ForeignKey(
        "companies.Department",
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="القسم",
    )
    employees = models.ManyToManyField(
        "employees.Employee",
        blank=True,
        related_name="holiday_rules",
        verbose_name="موظفين محددين",
    )

    # المعاملة
    treatment = models.CharField(
        max_length=20,
        choices=TREATMENT_CHOICES,
        default="paid_leave",
        verbose_name="نوع المعاملة",
    )

    # إعدادات المقابل الإضافي
    bonus_calc_method = models.CharField(
        max_length=20,
        choices=BONUS_CALC_CHOICES,
        blank=True,
        default="",
        verbose_name="طريقة حساب المقابل",
    )
    bonus_fixed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="المبلغ الثابت",
        help_text="مبلغ محدد بيتضاف على مرتب الموظف عن كل يوم اشتغله في الإجازة الرسمية",
    )
    bonus_salary_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="النسبة من المرتب %",
        help_text="نسبة مئوية من المرتب الأساسي الشهري بتتحسب عن كل يوم اشتغله في الإجازة الرسمية",
    )
    bonus_day_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=2.0,
        verbose_name="مضاعف أجر اليوم",
        help_text="أجر اليوم العادي مضروب في المضاعف ده",
    )

    priority = models.PositiveSmallIntegerField(
        default=10,
        verbose_name="الأولوية",
        help_text="رقم أصغر = أولوية أعلى. لو موظف ينطبق عليه أكتر من قاعدة، الأولوية الأعلى هي اللي تتطبق",
    )

    class Meta:
        ordering = ["priority", "id"]
        verbose_name = "قاعدة إجازة رسمية"
        verbose_name_plural = "قواعد الإجازات الرسمية"

    def __str__(self):
        return f"{self.holiday.name} → {self.get_scope_display()} → {self.get_treatment_display()}"

    def applies_to_employee(self, employee):
        """هل القاعدة دي بتنطبق على الموظف ده؟"""
        if self.scope == "company":
            return True
        if self.scope == "branch" and self.branch_id:
            return getattr(employee, "branch_id", None) == self.branch_id
        if self.scope == "department" and self.department_id:
            return getattr(employee, "department_id", None) == self.department_id
        if self.scope == "employees":
            return self.employees.filter(id=employee.id).exists()
        return False

    def calculate_bonus(self, daily_salary, basic_salary):
        """يحسب المقابل الإضافي ليوم واحد"""
        if self.treatment != "work_with_bonus":
            return 0.0
        if self.bonus_calc_method == "fixed_amount":
            return float(self.bonus_fixed_amount)
        elif self.bonus_calc_method == "salary_percentage":
            return round(float(basic_salary) * float(self.bonus_salary_percentage) / 100, 2)
        elif self.bonus_calc_method == "day_multiplier":
            return round(float(daily_salary) * float(self.bonus_day_multiplier), 2)
        return 0.0
