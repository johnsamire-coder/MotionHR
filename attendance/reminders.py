import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Helper — إرسال إشعار لمجموعة يوزرز
# ═══════════════════════════════════════════════════════
def _send_to_users(user_qs, title, body, data=None, title_en=None, body_en=None):
    """إرسال إشعار لقائمة يوزرز مع دعم عربي/إنجليزي حسب لغة التطبيق."""
    try:
        from attendance.fcm_logic import send_fcm_notification

        sent = 0
        for user in user_qs:
            try:
                ok = send_fcm_notification(
                    user,
                    title,
                    body,
                    data=data or {},
                    title_en=title_en,
                    body_en=body_en,
                )
                if ok is not False:
                    sent += 1
            except Exception as e:
                logger.error(f"FCM error for {getattr(user, 'username', user)}: {e}")
        return sent
    except Exception as e:
        logger.error(f"_send_to_users error: {e}")
        return 0




def _create_internal_notification_for_user(user, title, message, notification_type="general_notice", severity="info"):
    """إنشاء إشعار داخلي مرة واحدة فقط في اليوم لنفس الرسالة"""
    try:
        from employees.models import Employee
        from accounts.models import EmployeeNotification

        employee = Employee._base_manager.filter(user=user).first()
        if not employee:
            return False

        today = timezone.localdate()
        exists = EmployeeNotification.objects.filter(
            employee=employee,
            title=title,
            message=message,
            notification_type=notification_type,
            created_at__date=today,
        ).exists()

        if exists:
            return False

        EmployeeNotification.objects.create(
            employee=employee,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
        )
        return True
    except Exception as e:
        logger.error(f"_create_internal_notification_for_user error: {e}")
        return False

# ═══════════════════════════════════════════════════════
# 7.1  تذكير عدم تسجيل الحضور
# ═══════════════════════════════════════════════════════
def remind_missing_checkin():
    """
    يتشغل الساعة 10:00 صباحاً كل يوم عمل.
    بيشوف مين ماسجلش حضور لليوم ده.
    بيبعت إشعار للموظف + إشعار تجميعي للمدير.
    """
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Attendance

        User = get_user_model()
        today = timezone.localdate()

        # الجمعة والسبت عطلة
        if today.weekday() in (4, 5):
            logger.info("remind_missing_checkin: weekend — skipped")
            return

        logger.info(f"remind_missing_checkin: checking for {today}")

        employees = User.objects.filter(
            role__in=["employee", "manager", "hr_manager"],
            is_active=True,
        ).select_related("company")

        missing_by_company = {}

        for emp in employees:
            has_attendance = Attendance.objects.filter(
                employee__user=emp,
                date=today,
            ).exists()

            if not has_attendance:
                _send_to_users(
                    User.objects.filter(pk=emp.pk),
                    title="⏰ تذكير — تسجيل الحضور",
                    body="لم تسجل حضورك اليوم بعد. سجّل الآن من التطبيق.",
                    title_en="⏰ Reminder — Check-in",
                    body_en="You have not checked in today yet. Please check in now from the app.",
                    data={"type": "reminder_checkin", "date": str(today)},
                )

                cid = getattr(emp, "company_id", None)
                if cid:
                    missing_by_company.setdefault(cid, []).append(emp.get_full_name() or emp.username)

        for cid, names in missing_by_company.items():
            managers = User.objects.filter(
                company_id=cid,
                role__in=["company_admin", "manager", "hr_manager", "super_admin"],
                is_active=True,
            )
            count = len(names)

            sample_ar = "، ".join(names[:3])
            suffix_ar = " وآخرون..." if count > 3 else ""

            sample_en = ", ".join(names[:3])
            suffix_en = " and others..." if count > 3 else ""

            _send_to_users(
                managers,
                title=f"⚠️ {count} موظف لم يسجلوا الحضور",
                body=f"{sample_ar}{suffix_ar}",
                title_en=f"⚠️ {count} employees have not checked in",
                body_en=f"{sample_en}{suffix_en}",
                data={"type": "reminder_checkin_manager", "date": str(today), "count": str(count)},
            )

        logger.info("remind_missing_checkin: done")

    except Exception as e:
        logger.error(f"remind_missing_checkin error: {e}")


# ═══════════════════════════════════════════════════════
# 7.2  تذكير عدم تسجيل الانصراف
# ═══════════════════════════════════════════════════════
def remind_missing_checkout():
    """
    يتشغل الساعة 6:00 مساءً كل يوم عمل.
    بيشوف مين عنده check_in بس ماعندوش check_out.
    """
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Attendance

        User = get_user_model()
        today = timezone.localdate()

        if today.weekday() in (4, 5):
            logger.info("remind_missing_checkout: weekend — skipped")
            return

        logger.info(f"remind_missing_checkout: checking for {today}")

        pending = Attendance.objects.filter(
            date=today,
            check_in_time__isnull=False,
            check_out_time__isnull=True,
        ).select_related("employee__user", "employee__user__company")

        missing_by_company = {}

        for att in pending:
            emp_user = att.employee.user
            _send_to_users(
                User.objects.filter(pk=emp_user.pk),
                title="⏰ تذكير — تسجيل الانصراف",
                body="لم تسجل انصرافك بعد. سجّل الانصراف من التطبيق الآن.",
                title_en="⏰ Reminder — Check-out",
                body_en="You have not checked out yet. Please check out now from the app.",
                data={"type": "reminder_checkout", "date": str(today)},
            )

            cid = getattr(emp_user, "company_id", None)
            if cid:
                name = emp_user.get_full_name() or emp_user.username
                missing_by_company.setdefault(cid, []).append(name)

        for cid, names in missing_by_company.items():
            managers = User.objects.filter(
                company_id=cid,
                role__in=["company_admin", "manager", "hr_manager", "super_admin"],
                is_active=True,
            )
            count = len(names)

            sample_ar = "، ".join(names[:3])
            suffix_ar = " وآخرون..." if count > 3 else ""

            sample_en = ", ".join(names[:3])
            suffix_en = " and others..." if count > 3 else ""

            _send_to_users(
                managers,
                title=f"⚠️ {count} موظف لم يسجلوا الانصراف",
                body=f"{sample_ar}{suffix_ar}",
                title_en=f"⚠️ {count} employees have not checked out",
                body_en=f"{sample_en}{suffix_en}",
                data={"type": "reminder_checkout_manager", "date": str(today), "count": str(count)},
            )

        logger.info("remind_missing_checkout: done")

    except Exception as e:
        logger.error(f"remind_missing_checkout error: {e}")


# ═══════════════════════════════════════════════════════
# 7.3  تذكير طلبات معلقة عند المدير
# ═══════════════════════════════════════════════════════
def remind_pending_requests():
    """
    يتشغل كل يوم الساعة 11:00 صباحاً.
    بيشوف الطلبات اللي status=pending وعمرها > 24 ساعة.
    بيبعت إشعار للمدير المسؤول.
    """
    try:
        from django.contrib.auth import get_user_model
        from requests_app.models import EmployeeRequest

        User = get_user_model()
        threshold = timezone.now() - timedelta(hours=24)

        logger.info("remind_pending_requests: checking...")

        pending_by_company = {}

        pending_requests = EmployeeRequest.objects.filter(
            status="pending",
            created_at__lt=threshold,
        ).select_related("employee__user", "employee__user__company")

        for req in pending_requests:
            try:
                emp_user = req.employee.user
                cid = getattr(emp_user, "company_id", None)
                if cid:
                    name = emp_user.get_full_name() or emp_user.username
                    pending_by_company.setdefault(cid, {"count": 0, "names": []})
                    pending_by_company[cid]["count"] += 1
                    if name not in pending_by_company[cid]["names"]:
                        pending_by_company[cid]["names"].append(name)
            except Exception as e:
                logger.warning(f"Error processing request {req.id}: {e}")

        logger.info(
            f"remind_pending_requests: found {sum(v['count'] for v in pending_by_company.values())} pending requests"
        )

        for cid, info in pending_by_company.items():
            managers = User.objects.filter(
                company_id=cid,
                role__in=["company_admin", "manager", "hr_manager", "super_admin"],
                is_active=True,
            )
            count = info["count"]

            sample_ar = "، ".join(info["names"][:3])
            suffix_ar = " وآخرون..." if count > 3 else ""

            sample_en = ", ".join(info["names"][:3])
            suffix_en = " and others..." if count > 3 else ""

            _send_to_users(
                managers,
                title=f"📋 {count} طلب معلق ينتظر موافقتك",
                body=f"{sample_ar}{suffix_ar} — لم تتم مراجعتها منذ أكثر من 24 ساعة.",
                title_en=f"📋 {count} pending requests awaiting your approval",
                body_en=f"{sample_en}{suffix_en} — not reviewed for more than 24 hours.",
                data={"type": "reminder_pending_requests", "count": str(count)},
            )

        logger.info(f"remind_pending_requests: done — {len(pending_by_company)} companies notified")

    except Exception as e:
        logger.error(f"remind_pending_requests error: {e}")


# ═══════════════════════════════════════════════════════
# 7.4  تذكير موافقات اللائحة
# ═══════════════════════════════════════════════════════
def remind_charter_acceptance():
    """
    يتشغل كل يوم الساعة 9:30 صباحاً.
    بيشوف مين ماوافقش على اللائحة لحد دلوقتي.
    """
    try:
        from django.contrib.auth import get_user_model
        from companies.models import WorkCharter, CharterAcceptance

        User = get_user_model()

        logger.info("remind_charter_acceptance: checking...")

        charters = WorkCharter.objects.filter(is_active=True)
        total_notified = 0

        for charter in charters:
            accepted_user_ids = CharterAcceptance.objects.filter(
                charter=charter,
            ).values_list("employee__user_id", flat=True)

            pending_users = User.objects.filter(
                company=charter.company,
                role__in=["employee", "manager", "hr_manager"],
                is_active=True,
            ).exclude(id__in=accepted_user_ids)

            if not pending_users.exists():
                continue

            count = pending_users.count()

            for user in pending_users:
                _send_to_users(
                    User.objects.filter(pk=user.pk),
                    title="📄 تذكير — الموافقة على اللائحة",
                    body="لم توافق على اللائحة التنظيمية بعد. يرجى مراجعتها والموافقة من التطبيق.",
                    title_en="📄 Reminder — Charter Acceptance",
                    body_en="You have not accepted the work charter yet. Please review and accept it from the app.",
                    data={"type": "reminder_charter", "charter_id": str(charter.id)},
                )
                total_notified += 1

            managers = User.objects.filter(
                company=charter.company,
                role__in=["company_admin", "super_admin"],
                is_active=True,
            )
            _send_to_users(
                managers,
                title=f"📄 {count} موظف لم يوافقوا على اللائحة",
                body="تذكير: يوجد موظفون لم يوافقوا على اللائحة التنظيمية بعد.",
                title_en=f"📄 {count} employees have not accepted the charter",
                body_en="Reminder: there are employees who have not accepted the work charter yet.",
                data={"type": "reminder_charter_manager", "count": str(count)},
            )

        logger.info(f"remind_charter_acceptance: done — notified {total_notified} employees")

    except Exception as e:
        logger.error(f"remind_charter_acceptance error: {e}")


# ═══════════════════════════════════════════════════════
# 7.5  تذكير مستندات منتهية (Placeholder)
# ═══════════════════════════════════════════════════════
def remind_expiring_documents():
    """
    Placeholder — هيتفعل لما نضيف موديل المستندات لاحقاً.
    """
    logger.info("remind_expiring_documents: placeholder — skipped")
    pass




# ═══════════════════════════════════════════════════════
# 7.6  تذكير فترات split_fixed
# ═══════════════════════════════════════════════════════
def remind_split_fixed_periods():
    """
    split_fixed:
    - عند بداية الفترة: إشعار للموظف فقط (مرة واحدة)
    - بعد انتهاء السماحية: إشعار للموظف + المدير + HR (مرة واحدة)
    """
    try:
        from django.contrib.auth import get_user_model
        from employees.models import Employee
        from attendance.models import Attendance, AttendanceSession
        from attendance.api_mobile import get_active_shift, get_shift_periods

        User = get_user_model()
        today = timezone.localdate()
        now = timezone.now()

        logger.info(f"remind_split_fixed_periods: checking for {today}")

        employees = Employee._base_manager.filter(
            status='active'
        ).select_related('user', 'company')

        total_employee_reminders = 0
        total_escalations = 0

        for employee in employees:
            try:
                if not employee.user or not employee.company:
                    continue

                shift = get_active_shift(employee, today)
                if not shift or getattr(shift, 'shift_mode', 'fixed') != 'split_fixed':
                    continue

                periods = get_shift_periods(shift, today)
                if not periods:
                    continue

                attendance = Attendance._base_manager.filter(
                    employee=employee,
                    date=today
                ).first()

                sessions = AttendanceSession._base_manager.none()
                if attendance:
                    sessions = AttendanceSession._base_manager.filter(
                        attendance=attendance,
                        employee=employee
                    ).order_by('session_number')

                grace_minutes = int(getattr(shift, 'grace_period', 0) or 0)

                for period in periods:
                    period_number = period.get('period_number', 1)
                    period_name = period.get('name') or f'الفترة {period_number}'
                    period_start = period.get('start')
                    period_end = period.get('end')
                    period_start_str = period.get('start_str', '')
                    period_end_str = period.get('end_str', '')

                    if not period_start or not period_end:
                        continue

                    # هل الموظف سجل حضور داخل الفترة دي؟
                    covered = False
                    for session in sessions:
                        check_in_time = getattr(session, 'check_in_time', None)
                        if check_in_time and period_start <= check_in_time <= period_end:
                            covered = True
                            break

                    if covered:
                        continue

                    # 1) بداية الفترة → للموظف فقط
                    if now >= period_start:
                        title_ar = f'⏰ تذكير: {period_name}'
                        body_ar = f'ابدأ تسجيل حضورك الآن في {period_name} ({period_start_str} - {period_end_str}) من شيفت {shift.name}'
                        title_en = f'⏰ Reminder: {period_name}'
                        body_en = f'Please check in now for {period_name} ({period_start_str} - {period_end_str}) from shift {shift.name}'

                        created = _create_internal_notification_for_user(
                            employee.user,
                            title_ar,
                            body_ar,
                            notification_type='general_notice',
                            severity='info',
                        )

                        if created:
                            _send_to_users(
                                User.objects.filter(pk=employee.user.pk),
                                title=title_ar,
                                body=body_ar,
                                title_en=title_en,
                                body_en=body_en,
                                data={
                                    "type": "split_period_start_reminder",
                                    "screen": "attendance",
                                    "date": str(today),
                                    "period_number": str(period_number),
                                },
                            )
                            total_employee_reminders += 1

                    # 2) بعد انتهاء السماحية → للموظف + المدير + HR
                    grace_end = period_start + timedelta(minutes=grace_minutes)
                    if now >= grace_end:
                        emp_name = getattr(employee, 'full_name_ar', '') or str(employee)

                        # إشعار الموظف
                        emp_title_ar = f'🚨 فاتتك {period_name}'
                        emp_body_ar = f'لم تسجل حضورك في {period_name} ({period_start_str} - {period_end_str}) من شيفت {shift.name}'
                        emp_title_en = f'🚨 Missed {period_name}'
                        emp_body_en = f'You missed check-in for {period_name} ({period_start_str} - {period_end_str}) from shift {shift.name}'

                        emp_created = _create_internal_notification_for_user(
                            employee.user,
                            emp_title_ar,
                            emp_body_ar,
                            notification_type='late_warning',
                            severity='danger',
                        )

                        if emp_created:
                            _send_to_users(
                                User.objects.filter(pk=employee.user.pk),
                                title=emp_title_ar,
                                body=emp_body_ar,
                                title_en=emp_title_en,
                                body_en=emp_body_en,
                                data={
                                    "type": "split_period_missed_employee",
                                    "screen": "attendance",
                                    "date": str(today),
                                    "period_number": str(period_number),
                                },
                            )

                        # إشعار المدير + HR + company_admin
                        managers = User.objects.filter(
                            company=employee.company,
                            role__in=["company_admin", "manager", "hr_manager", "super_admin"],
                            is_active=True,
                        )

                        mgr_title_ar = f'🚨 الموظف {emp_name} لم يسجل {period_name}'
                        mgr_body_ar = f'شيفت: {shift.name} | الفترة: {period_start_str} - {period_end_str}'
                        mgr_title_en = f'🚨 {emp_name} missed {period_name}'
                        mgr_body_en = f'Shift: {shift.name} | Period: {period_start_str} - {period_end_str}'

                        manager_sent_once = False
                        for manager in managers:
                            created_mgr = _create_internal_notification_for_user(
                                manager,
                                mgr_title_ar,
                                mgr_body_ar,
                                notification_type='general_notice',
                                severity='danger',
                            )
                            if created_mgr:
                                manager_sent_once = True

                        if manager_sent_once:
                            _send_to_users(
                                managers,
                                title=mgr_title_ar,
                                body=mgr_body_ar,
                                title_en=mgr_title_en,
                                body_en=mgr_body_en,
                                data={
                                    "type": "split_period_missed_manager",
                                    "screen": "manager_attendance",
                                    "date": str(today),
                                    "employee_id": str(employee.id),
                                    "period_number": str(period_number),
                                },
                            )
                            total_escalations += 1

            except Exception as emp_error:
                logger.error(f"remind_split_fixed_periods employee error: {emp_error}")

        logger.info(
            f"remind_split_fixed_periods: done - reminders={total_employee_reminders}, escalations={total_escalations}"
        )

    except Exception as e:
        logger.error(f"remind_split_fixed_periods error: {e}")



# ═══════════════════════════════════════════════════════
# 7.7  تنبيه فجوات تغطية الشيفتات للمديرين
# ═══════════════════════════════════════════════════════
def remind_shift_coverage_gaps():
    """
    يتشغل كل يوم الساعة 8:00 صباحاً.
    بيشوف كل التناوبات النشطة ويتحقق من التغطية.
    لو فيه فجوات → يبعت إشعار للمديرين.
    """
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import ShiftRotation, ShiftRotationSlot

        User = get_user_model()
        today = timezone.localdate()

        logger.info("remind_shift_coverage_gaps: checking...")

        rotations = ShiftRotation._base_manager.filter(is_active=True)
        total_alerts = 0

        for rotation in rotations:
            try:
                slots = list(
                    ShiftRotationSlot._base_manager.filter(
                        rotation=rotation,
                        company=rotation.company,
                    ).order_by('start_day_index', 'id')
                )

                covered_days = set()
                overlap_days = set()
                invalid_slot_ids = []
                missing_shift_slot_ids = []

                for slot in slots:
                    try:
                        start_idx = int(slot.start_day_index)
                        end_idx = int(slot.end_day_index)
                    except (TypeError, ValueError):
                        invalid_slot_ids.append(slot.id)
                        continue

                    if start_idx < 0 or end_idx < 0 or start_idx > end_idx or end_idx >= rotation.cycle_length_days:
                        invalid_slot_ids.append(slot.id)
                        continue

                    if not slot.shift_id:
                        missing_shift_slot_ids.append(slot.id)

                    slot_days = set(range(start_idx, end_idx + 1))
                    overlap_days.update(slot_days & covered_days)
                    covered_days.update(slot_days)

                missing_days = [day for day in range(rotation.cycle_length_days) if day not in covered_days]
                coverage_ok = not invalid_slot_ids and not overlap_days and not missing_days and not missing_shift_slot_ids

                if coverage_ok:
                    continue

                # فيه مشكلة → نبعت للمديرين
                problems = []
                if missing_days:
                    problems.append(f"أيام غير مغطاة: {missing_days}")
                if overlap_days:
                    problems.append(f"تداخل في أيام: {sorted(overlap_days)}")
                if invalid_slot_ids:
                    problems.append(f"slots غير صالحة: {len(invalid_slot_ids)}")
                if missing_shift_slot_ids:
                    problems.append(f"slots بدون شيفت: {len(missing_shift_slot_ids)}")

                problem_text = " | ".join(problems)

                title_ar = f'⚠️ تناوب "{rotation.name}" فيه فجوات في التغطية'
                body_ar = f"يرجى مراجعة التناوب وإصلاح التغطية. {problem_text}"
                title_en = f'⚠️ Rotation "{rotation.name}" has coverage gaps'
                body_en = f"Please review the rotation and fix coverage. {problem_text}"

                managers = User.objects.filter(
                    company=rotation.company,
                    role__in=["company_admin", "manager", "hr_manager", "super_admin"],
                    is_active=True,
                )

                sent_once = False
                for manager in managers:
                    created = _create_internal_notification_for_user(
                        manager,
                        title_ar,
                        body_ar,
                        notification_type='general_notice',
                        severity='warning',
                    )
                    if created:
                        sent_once = True

                if sent_once:
                    _send_to_users(
                        managers,
                        title=title_ar,
                        body=body_ar,
                        title_en=title_en,
                        body_en=body_en,
                        data={
                            "type": "shift_coverage_gap",
                            "screen": "shifts",
                            "rotation_id": str(rotation.id),
                            "date": str(today),
                        },
                    )
                    total_alerts += 1

            except Exception as rot_err:
                logger.error(f"remind_shift_coverage_gaps rotation error: {rot_err}")

        logger.info(f"remind_shift_coverage_gaps: done — alerts={total_alerts}")

    except Exception as e:
        logger.error(f"remind_shift_coverage_gaps error: {e}")

# ═══════════════════════════════════════════════════════
# الدالة الرئيسية — بيتم استدعاؤها من Cron
# ═══════════════════════════════════════════════════════
def run_all_reminders(reminder_type="all"):
    """
    نقطة الدخول الرئيسية.
    reminder_type: all | checkin | checkout | pending | charter | documents | split_periods
    """
    logger.info(f"=== MotionHR Reminders — type={reminder_type} ===")

    dispatch = {
        "checkin": remind_missing_checkin,
        "checkout": remind_missing_checkout,
        "pending": remind_pending_requests,
        "charter": remind_charter_acceptance,
        "documents": remind_expiring_documents,
        "split_periods": remind_split_fixed_periods,
        "shift_coverage": remind_shift_coverage_gaps,
    }

    if reminder_type == "all":
        for name, func in dispatch.items():
            try:
                logger.info(f"Running: {name}")
                func()
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
    elif reminder_type in dispatch:
        dispatch[reminder_type]()
    else:
        logger.error(f"Unknown reminder_type: {reminder_type}")

    logger.info("=== Reminders Done ===")
