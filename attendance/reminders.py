import logging
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Helper — إرسال إشعار لمجموعة يوزرز
# ═══════════════════════════════════════════════════════
def _send_to_users(user_qs, title, body, data=None):
    """إرسال إشعار لقائمة يوزرز"""
    try:
        from accounts.fcm_service import send_fcm_notification
        from accounts.fcm_models import FCMDeviceToken, NotificationLog

        sent = 0
        for user in user_qs:
            tokens = FCMDeviceToken.objects.filter(user=user, is_active=True)
            for token_obj in tokens:
                try:
                    send_fcm_notification(
                        token=token_obj.token,
                        title=title,
                        body=body,
                        data=data or {},
                    )
                    NotificationLog.objects.create(
                        user=user,
                        title=title,
                        body=body,
                        notification_type=data.get("type", "reminder") if data else "reminder",
                    )
                    sent += 1
                except Exception as e:
                    logger.error(f"FCM error for {user.username}: {e}")
        return sent
    except Exception as e:
        logger.error(f"_send_to_users error: {e}")
        return 0


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
        from attendance.models import Attendance, EmployeeShift

        User = get_user_model()
        today = timezone.localdate()

        # مش في الويكند (5=السبت, 6=الأحد)
        if today.weekday() in (4, 5):  # الجمعة والسبت عطلة
            logger.info("remind_missing_checkin: weekend — skipped")
            return

        logger.info(f"remind_missing_checkin: checking for {today}")

        # كل الموظفين النشطين (role=employee)
        employees = User.objects.filter(
            role__in=["employee", "manager", "hr_manager"],
            is_active=True,
        ).select_related("company")

        missing_by_company = {}  # company_id -> list of employees

        for emp in employees:
            # هل سجل حضور النهارده؟
            has_attendance = Attendance.objects.filter(
                employee__user=emp,
                date=today,
            ).exists()

            if not has_attendance:
                # بعت إشعار للموظف
                _send_to_users(
                    User.objects.filter(pk=emp.pk),
                    title="⏰ تذكير — تسجيل الحضور",
                    body="لم تسجل حضورك اليوم بعد. سجّل الآن من التطبيق.",
                    data={"type": "reminder_checkin", "date": str(today)},
                )

                # تجميع للمدير
                cid = emp.company_id if hasattr(emp, "company_id") else None
                if cid:
                    missing_by_company.setdefault(cid, []).append(emp.get_full_name() or emp.username)

        # إشعار تجميعي للمديرين
        for cid, names in missing_by_company.items():
            managers = User.objects.filter(
                company_id=cid,
                role__in=["company_admin", "manager", "hr_manager", "super_admin"],
                is_active=True,
            )
            count = len(names)
            sample = "، ".join(names[:3])
            suffix = f" وآخرون..." if count > 3 else ""
            _send_to_users(
                managers,
                title=f"⚠️ {count} موظف لم يسجلوا الحضور",
                body=f"{sample}{suffix}",
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

        # سجلوا حضور بس مسجلوش انصراف
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
                data={"type": "reminder_checkout", "date": str(today)},
            )

            cid = emp_user.company_id if hasattr(emp_user, "company_id") else None
            if cid:
                name = emp_user.get_full_name() or emp_user.username
                missing_by_company.setdefault(cid, []).append(name)

        # إشعار تجميعي للمديرين
        for cid, names in missing_by_company.items():
            managers = User.objects.filter(
                company_id=cid,
                role__in=["company_admin", "manager", "hr_manager", "super_admin"],
                is_active=True,
            )
            count = len(names)
            sample = "، ".join(names[:3])
            suffix = " وآخرون..." if count > 3 else ""
            _send_to_users(
                managers,
                title=f"⚠️ {count} موظف لم يسجلوا الانصراف",
                body=f"{sample}{suffix}",
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
    الموديل الحقيقي: EmployeeRequest (requests_app)
    """
    try:
        from django.contrib.auth import get_user_model
        from requests_app.models import EmployeeRequest

        User = get_user_model()
        threshold = timezone.now() - timedelta(hours=24)

        logger.info("remind_pending_requests: checking...")

        pending_by_company = {}

        # جلب كل الطلبات المعلقة منذ أكثر من 24 ساعة
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

        logger.info(f"remind_pending_requests: found {sum(v['count'] for v in pending_by_company.values())} pending requests")

        # إرسال للمديرين
        for cid, info in pending_by_company.items():
            managers = User.objects.filter(
                company_id=cid,
                role__in=["company_admin", "manager", "hr_manager", "super_admin"],
                is_active=True,
            )
            count = info["count"]
            sample = "، ".join(info["names"][:3])
            suffix = " وآخرون..." if count > 3 else ""
            _send_to_users(
                managers,
                title=f"📋 {count} طلب معلق ينتظر موافقتك",
                body=f"{sample}{suffix} — لم تتم مراجعتها منذ أكثر من 24 ساعة.",
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

        # جلب كل اللوائح الشغالة
        charters = WorkCharter.objects.filter(is_active=True)

        total_notified = 0

        for charter in charters:
            # مين وافق فعلاً
            accepted_user_ids = CharterAcceptance.objects.filter(
                charter=charter,
            ).values_list("employee__user_id", flat=True)

            # الموظفين في نفس الشركة اللي ماوافقوش
            pending_users = User.objects.filter(
                company=charter.company,
                role__in=["employee", "manager", "hr_manager"],
                is_active=True,
            ).exclude(id__in=accepted_user_ids)

            if not pending_users.exists():
                continue

            count = pending_users.count()

            # إشعار لكل موظف لم يوافق
            for user in pending_users:
                _send_to_users(
                    User.objects.filter(pk=user.pk),
                    title="📄 تذكير — الموافقة على اللائحة",
                    body=f"لم توافق على اللائحة التنظيمية بعد. يرجى مراجعتها والموافقة من التطبيق.",
                    data={"type": "reminder_charter", "charter_id": str(charter.id)},
                )
                total_notified += 1

            # إشعار للمدير
            managers = User.objects.filter(
                company=charter.company,
                role__in=["company_admin", "super_admin"],
                is_active=True,
            )
            _send_to_users(
                managers,
                title=f"📄 {count} موظف لم يوافقوا على اللائحة",
                body="تذكير: يوجد موظفون لم يوافقوا على اللائحة التنظيمية بعد.",
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
    Placeholder — هيتفعل لما نضيف موديل المستندات في المرحلة 6.
    يتشغل كل يوم الساعة 8:00 صباحاً.
    """
    logger.info("remind_expiring_documents: placeholder — skipped (Phase 6 not done yet)")
    pass


# ═══════════════════════════════════════════════════════
# الدالة الرئيسية — بيتم استدعاؤها من Cron
# ═══════════════════════════════════════════════════════
def run_all_reminders(reminder_type="all"):
    """
    نقطة الدخول الرئيسية.
    reminder_type: all | checkin | checkout | pending | charter | documents
    """
    logger.info(f"=== MotionHR Reminders — type={reminder_type} ===")

    dispatch = {
        "checkin":   remind_missing_checkin,
        "checkout":  remind_missing_checkout,
        "pending":   remind_pending_requests,
        "charter":   remind_charter_acceptance,
        "documents": remind_expiring_documents,
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
