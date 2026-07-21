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
            
            if success:
                sent_count += 1
        except Exception as e:
            # لو حصل خطأ لموظف معين، سيبه وكمل الباقيين
            print(f"❌ Failed to send to {employee}: {e}")
            continue
    
    return sent_count

