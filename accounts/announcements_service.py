"""
Announcements Service - خدمة إرسال إشعارات الشركة للموظفين
"""
from accounts.fcm_service import send_notification_to_user


def broadcast_announcement(announcement):
    """
    إرسال إشعار الشركة لكل الموظفين المستهدفين
    
    Args:
        announcement: CompanyAnnouncement instance
    
    Returns:
        int: عدد الموظفين اللي وصلهم الإشعار بنجاح
    """
    sent_count = 0
    
    # 1. جيب الموظفين المستهدفين (باستخدام method الموديل الجاهزة)
    target_employees = announcement.get_target_employees()
    
    # 2. لف على كل موظف وابعتله الإشعار
    for employee in target_employees:
        # لازم يكون عنده User مرتبط بيه عشان نبعت له
        if not employee.user:
            continue
        
        try:
            # ابعت Push Notification
            success = send_notification_to_user(
                user=employee.user,
                title=announcement.title,
                body=announcement.message,
                data={
                    'type': 'company_announcement',
                    'announcement_id': str(announcement.id),
                    'announcement_type': announcement.announcement_type,
                    'priority': announcement.priority,
                }
            )
            
            # الدالة بترجع dict، فالنجاح هو إن فيه جهاز وصله فعلاً
            if isinstance(success, dict) and success.get('sent', 0) > 0:
                sent_count += 1
        except Exception as e:
            # لو حصل خطأ لموظف معين، سيبه وكمل الباقيين
            print(f"❌ Failed to send to {employee}: {e}")
            continue
    
    return sent_count



def broadcast_system_announcement(announcement):
    """
    إشعار النظام (من لوحة الأدمن) لكل المستخدمين النشطين اللي عندهم موبايل متسجل.
    الشركات الموقوفة بتتخطى لوحدها. بترجع عدد اللي وصلهم.
    """
    from accounts.fcm_models import FCMDeviceToken
    from accounts.models import User
    if not getattr(announcement, 'send_to_all', True):
        return 0
    user_ids = FCMDeviceToken._default_manager.values_list('user_id', flat=True).distinct()
    sent_count = 0
    for user in User._base_manager.filter(id__in=user_ids, is_active=True):
        try:
            result = send_notification_to_user(
                user=user,
                title=announcement.title,
                body=announcement.message,
                data={'type': 'system_announcement', 'announcement_id': str(announcement.id)},
            )
            if isinstance(result, dict) and result.get('sent', 0) > 0:
                sent_count += 1
        except Exception as e:
            print(f"❌ Failed to send to {user}: {e}")
    return sent_count
