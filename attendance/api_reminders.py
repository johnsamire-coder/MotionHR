from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

ALLOWED_ROLES = {"super_admin", "company_admin", "manager", "hr_manager"}


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def trigger_reminder(request):
    """
    POST /attendance/api/mobile/manager/reminders/trigger/
    body: {"type": "checkin" | "checkout" | "pending" | "charter" | "all"}
    """
    if getattr(request.user, "role", None) not in ALLOWED_ROLES:
        return Response({"error": "غير مصرح"}, status=status.HTTP_403_FORBIDDEN)

    reminder_type = request.data.get("type", "all")
    valid_types = ["all", "checkin", "checkout", "pending", "charter", "documents"]

    if reminder_type not in valid_types:
        return Response(
            {"error": f"النوع غير صحيح. الأنواع المتاحة: {valid_types}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from attendance.reminders import run_all_reminders
        run_all_reminders(reminder_type=reminder_type)
        return Response({
            "success": True,
            "message": f"تم إرسال التذكيرات: {reminder_type}",
            "type": reminder_type,
        })
    except Exception as e:
        logger.exception("trigger_reminder error")
        return Response(
            {"error": "فشل إرسال التذكيرات", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def reminder_settings(request):
    """
    GET /attendance/api/mobile/manager/reminders/settings/
    """
    if getattr(request.user, "role", None) not in ALLOWED_ROLES:
        return Response({"error": "غير مصرح"}, status=status.HTTP_403_FORBIDDEN)

    settings_data = {
        "reminders": [
            {
                "type": "checkin",
                "name": "تذكير الحضور",
                "description": "يُرسل للموظفين الذين لم يسجلوا حضورهم",
                "schedule": "10:00 صباحاً — الأحد-الخميس",
                "enabled": True,
            },
            {
                "type": "checkout",
                "name": "تذكير الانصراف",
                "description": "يُرسل للموظفين الذين لم يسجلوا انصرافهم",
                "schedule": "6:00 مساءً — الأحد-الخميس",
                "enabled": True,
            },
            {
                "type": "pending",
                "name": "الطلبات المعلقة",
                "description": "يُرسل للمدير عن الطلبات المعلقة أكثر من 24 ساعة",
                "schedule": "11:00 صباحاً — الأحد-الخميس",
                "enabled": True,
            },
            {
                "type": "charter",
                "name": "موافقات اللائحة",
                "description": "يُرسل للموظفين الذين لم يوافقوا على اللائحة",
                "schedule": "9:30 صباحاً — الأحد-الخميس",
                "enabled": True,
            },
            {
                "type": "documents",
                "name": "المستندات المنتهية",
                "description": "تنبيه مستندات تنتهي خلال 30 يوم",
                "schedule": "8:00 صباحاً — يومياً",
                "enabled": False,
                "note": "يتطلب المرحلة 6 (ملف الموظف)",
            },
        ],
        "timezone": "Africa/Cairo",
        "working_days": ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"],
    }

    return Response(settings_data)
