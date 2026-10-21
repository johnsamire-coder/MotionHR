"""
upload_validation.py
فحص موحّد للملفات المرفوعة: الامتداد والنوع والحجم، والصور لازم تكون صور فعلاً.
"""
import os

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.gif'}
DOCUMENT_EXTS = IMAGE_EXTS | {'.pdf', '.doc', '.docx', '.xls', '.xlsx'}

IMAGE_MAX_MB = 10
DOCUMENT_MAX_MB = 25


def upload_error(uploaded_file, kind='document'):
    """بترجع رسالة الخطأ، أو None لو الملف تمام. kind: image | document"""
    if uploaded_file is None:
        return 'لم يتم إرفاق ملف'
    allowed = IMAGE_EXTS if kind == 'image' else DOCUMENT_EXTS
    max_mb = IMAGE_MAX_MB if kind == 'image' else DOCUMENT_MAX_MB
    ext = os.path.splitext((uploaded_file.name or '').lower())[1]
    if ext not in allowed:
        names = 'صور (JPG / PNG / WEBP)' if kind == 'image' else 'PDF / Word / Excel / صور'
        return f'نوع الملف غير مسموح ({ext or "من غير امتداد"}). المسموح: {names}'
    if (uploaded_file.size or 0) > max_mb * 1024 * 1024:
        return f'الملف كبير جداً. الحد الأقصى {max_mb} ميجا'
    if ext in IMAGE_EXTS and ext != '.heic':
        try:
            from PIL import Image
            pos = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else 0
            Image.open(uploaded_file).verify()
            uploaded_file.seek(pos)
        except Exception:
            return 'الملف ده مش صورة سليمة'
    return None
