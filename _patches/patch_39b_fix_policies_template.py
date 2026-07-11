#!/usr/bin/env python3
"""
Patch 39b: Fix Policies Template
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 39b: Fix Policies Template")
print("=" * 60)

template_content = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}السياسات والقواعد{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      <i class="bi bi-sliders me-2" style="color:#06B6D4;"></i>
      السياسات والقواعد
    </h4>
    <p class="text-muted mb-0">
      حدّد قواعد الشركة الخاصة بالحضور، التأخير، الأذونات، الأوفر تايم، وصلاحيات HR
    </p>
  </div>

  <form method="post">
    {% csrf_token %}

    <div class="row g-4">

      <!-- سياسة التأخير -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-clock-history me-2" style="color:#f59e0b;"></i>
              سياسة التأخير
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <div class="mb-3">
              <label class="form-label fw-semibold small">سماحية التأخير (دقيقة)</label>
              <select name="grace_period_minutes" class="form-select">
                <option value="5"  {% if policy.grace_period_minutes == 5 %}selected{% endif %}>5 دقائق</option>
                <option value="10" {% if policy.grace_period_minutes == 10 %}selected{% endif %}>10 دقائق</option>
                <option value="15" {% if policy.grace_period_minutes == 15 %}selected{% endif %}>15 دقيقة</option>
                <option value="20" {% if policy.grace_period_minutes == 20 %}selected{% endif %}>20 دقيقة</option>
                <option value="30" {% if policy.grace_period_minutes == 30 %}selected{% endif %}>30 دقيقة</option>
              </select>
            </div>

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="reset_late_counter_monthly" id="resetLate"
                     {% if policy.reset_late_counter_monthly %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="resetLate">
                تصفير عداد التأخير شهريًا
              </label>
            </div>

            <div class="row g-2">
              <div class="col-md-6">
                <label class="form-label small">أول إنذار بعد</label>
                <input type="number" name="late_first_warning_after_count"
                       class="form-control" value="{{ policy.late_first_warning_after_count }}" min="1">
              </div>
              <div class="col-md-6">
                <label class="form-label small">ثاني إنذار بعد</label>
                <input type="number" name="late_second_warning_after_count"
                       class="form-control" value="{{ policy.late_second_warning_after_count }}" min="1">
              </div>
              <div class="col-md-4">
                <label class="form-label small">ربع يوم بعد</label>
                <input type="number" name="late_quarter_day_deduction_after_count"
                       class="form-control" value="{{ policy.late_quarter_day_deduction_after_count }}" min="1">
              </div>
              <div class="col-md-4">
                <label class="form-label small">نصف يوم بعد</label>
                <input type="number" name="late_half_day_deduction_after_count"
                       class="form-control" value="{{ policy.late_half_day_deduction_after_count }}" min="1">
              </div>
              <div class="col-md-4">
                <label class="form-label small">يوم كامل بعد</label>
                <input type="number" name="late_full_day_deduction_after_count"
                       class="form-control" value="{{ policy.late_full_day_deduction_after_count }}" min="1">
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- سياسة الأذونات -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-hourglass-split me-2" style="color:#10b981;"></i>
              سياسة الأذونات
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="permission_enabled" id="permEnabled"
                     {% if policy.permission_enabled %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="permEnabled">
                الأذونات مفعلة
              </label>
            </div>

            <div class="row g-2">
              <div class="col-md-6">
                <label class="form-label small">عدد الأذونات شهريًا</label>
                <input type="number" name="permission_monthly_limit"
                       class="form-control" value="{{ policy.permission_monthly_limit }}" min="0">
              </div>
              <div class="col-md-6">
                <label class="form-label small">أقصى ساعات للإذن الواحد</label>
                <input type="number" step="0.5" name="permission_max_hours_per_request"
                       class="form-control" value="{{ policy.permission_max_hours_per_request }}" min="0">
              </div>
            </div>

            <div class="form-check form-switch mt-3">
              <input class="form-check-input" type="checkbox"
                     name="permission_requires_approval" id="permApproval"
                     {% if policy.permission_requires_approval %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="permApproval">
                الإذن يحتاج موافقة
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- سياسة الأوفر تايم -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-lightning-charge me-2" style="color:#7c3aed;"></i>
              سياسة الأوفر تايم
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="overtime_enabled" id="otEnabled"
                     {% if policy.overtime_enabled %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="otEnabled">
                الأوفر تايم مفعّل
              </label>
            </div>

            <div class="row g-2">
              <div class="col-md-6">
                <label class="form-label small">يبدأ بعد (دقيقة)</label>
                <input type="number" name="overtime_start_after_minutes"
                       class="form-control" value="{{ policy.overtime_start_after_minutes }}" min="0">
              </div>
              <div class="col-md-6">
                <label class="form-label small">أقصى أوفر تايم يومي</label>
                <input type="number" step="0.5" name="overtime_daily_max_hours"
                       class="form-control" value="{{ policy.overtime_daily_max_hours }}" min="0">
              </div>
              <div class="col-md-6">
                <label class="form-label small">أقصى أوفر تايم شهري</label>
                <input type="number" step="0.5" name="overtime_monthly_max_hours"
                       class="form-control" value="{{ policy.overtime_monthly_max_hours }}" min="0">
              </div>
            </div>

            <div class="form-check form-switch mt-3">
              <input class="form-check-input" type="checkbox"
                     name="overtime_requires_approval" id="otApproval"
                     {% if policy.overtime_requires_approval %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="otApproval">
                يحتاج موافقة المدير
              </label>
            </div>

            <div class="form-check form-switch mt-2">
              <input class="form-check-input" type="checkbox"
                     name="overtime_requires_reason" id="otReason"
                     {% if policy.overtime_requires_reason %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="otReason">
                الموظف لازم يكتب السبب
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- سياسة الموقع -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-geo-alt me-2" style="color:#06B6D4;"></i>
              سياسة الحضور بالموقع
            </h5>
          </div>
          <div class="card-body px-4 pb-4">

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="checkin_requires_location" id="gpsRequired"
                     {% if policy.checkin_requires_location %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="gpsRequired">
                الحضور يحتاج GPS
              </label>
            </div>

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="checkin_requires_branch_range" id="rangeRequired"
                     {% if policy.checkin_requires_branch_range %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="rangeRequired">
                الحضور لازم يكون داخل نطاق الفرع
              </label>
            </div>

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="checkout_from_anywhere" id="checkoutAnywhere"
                     {% if policy.checkout_from_anywhere %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="checkoutAnywhere">
                الانصراف من أي مكان
              </label>
            </div>

            <div class="row g-2">
              <div class="col-md-6">
                <label class="form-label small">النطاق الافتراضي (متر)</label>
                <input type="number" name="default_checkin_radius"
                       class="form-control" value="{{ policy.default_checkin_radius }}" min="0">
                <small class="text-muted">يمكن تغييره لكل فرع</small>
              </div>
              <div class="col-md-6">
                <label class="form-label small">سماحية مسافة إضافية (متر)</label>
                <input type="number" name="distance_tolerance_meters"
                       class="form-control" value="{{ policy.distance_tolerance_meters }}" min="0">
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- الغياب + صلاحيات HR -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-person-x me-2" style="color:#ef4444;"></i>
              الغياب وصلاحيات HR
            </h5>
          </div>
          <div class="card-body px-4 pb-4">

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="auto_absence_enabled" id="autoAbsence"
                     {% if policy.auto_absence_enabled %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="autoAbsence">
                تفعيل الغياب التلقائي
              </label>
            </div>

            <div class="mb-3">
              <label class="form-label small">بعد الساعة يعتبر غياب</label>
              <input type="time" name="auto_absence_after_time"
                     class="form-control"
                     value="{{ policy.auto_absence_after_time|time:'H:i'|default:'' }}">
            </div>

            <hr>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="hr_can_cancel_attendance" id="hrCancel"
                     {% if policy.hr_can_cancel_attendance %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="hrCancel">
                HR يقدر يلغي حضور/انصراف
              </label>
            </div>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="hr_can_edit_attendance" id="hrEdit"
                     {% if policy.hr_can_edit_attendance %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="hrEdit">
                HR يقدر يعدل الحضور
              </label>
            </div>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="attendance_edit_reason_required" id="editReason"
                     {% if policy.attendance_edit_reason_required %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="editReason">
                سبب التعديل إجباري
              </label>
            </div>

            <div class="form-check form-switch mt-3">
              <input class="form-check-input" type="checkbox"
                     name="manager_can_see_financial_requests" id="mgrFinancial"
                     {% if policy.manager_can_see_financial_requests %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="mgrFinancial">
                المدير يشوف الطلبات المالية
              </label>
            </div>

          </div>
        </div>
      </div>

      <!-- ملاحظات -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-journal-text me-2" style="color:#6b7280;"></i>
              ملاحظات إضافية
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <textarea name="notes" class="form-control" rows="10"
                      placeholder="أي سياسات أو ملاحظات إضافية...">{{ policy.notes }}</textarea>
          </div>
        </div>
      </div>

    </div>

    <div class="mt-4">
      <button type="submit" class="btn btn-lg text-white px-5"
              style="background:#06B6D4; border-radius:12px;">
        <i class="bi bi-check-lg me-2"></i>
        حفظ السياسات
      </button>
    </div>

  </form>

</div>
{% endblock %}
"""

write_file(
    os.path.join(BASE_DIR, "templates", "companies", "policies.html"),
    template_content
)

print("\n" + "=" * 60)
print("  ✅ Patch 39b اكتمل!")
print("=" * 60)
print("""
اللي اتصلح:
  ✅ شلنا split filter من policies.html
  ✅ صفحة السياسات لازم تفتح عادي دلوقتي

جرب:
  /companies/policies/
""")