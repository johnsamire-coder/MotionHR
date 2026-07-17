# -*- coding: utf-8 -*-
"""
API for File Attachments (Phase 4)
Universal attachment system for any model
"""

import os
import io
from PIL import Image
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import authentication_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from core.models import Attachment


# ═════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════

MAX_FILE_SIZE_MB = 25
MAX_FILES_PER_OBJECT = 10
MAX_TOTAL_SIZE_MB = 100

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic"}
ALLOWED_PDF_TYPES = {"application/pdf"}
ALLOWED_WORD_TYPES = {
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXCEL_TYPES = {
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

ALL_ALLOWED_TYPES = (
    ALLOWED_IMAGE_TYPES
    | ALLOWED_PDF_TYPES
    | ALLOWED_WORD_TYPES
    | ALLOWED_EXCEL_TYPES
)

# Model mapping (app_label.ModelName)
ALLOWED_MODELS = {
    "leaves.LeaveRequest": "leaves",
    "requests_app.EmployeeRequest": "requests_app",
}


# ═════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════

def get_file_type(mime_type):
    """Determine file_type based on MIME"""
    if mime_type in ALLOWED_IMAGE_TYPES:
        return "image"
    if mime_type in ALLOWED_PDF_TYPES:
        return "pdf"
    if mime_type in ALLOWED_WORD_TYPES:
        return "word"
    if mime_type in ALLOWED_EXCEL_TYPES:
        return "excel"
    return "other"


def validate_file(uploaded_file):
    """Validate file size and type"""
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"الملف كبير جداً. الحد الأقصى {MAX_FILE_SIZE_MB} MB"

    mime_type = uploaded_file.content_type
    if mime_type not in ALL_ALLOWED_TYPES:
        return False, f"نوع الملف غير مسموح: {mime_type}"

    return True, None


def compress_image(uploaded_file, max_size_mb=2, quality=85):
    """Compress image while preserving quality"""
    try:
        img = Image.open(uploaded_file)

        # Convert RGBA to RGB (for JPEG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize if larger than 2000px
        max_dimension = 2000
        if img.width > max_dimension or img.height > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

        # Save to buffer
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)

        # Check size, reduce quality if still too big
        while output.tell() > max_size_mb * 1024 * 1024 and quality > 30:
            quality -= 10
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            output.seek(0)

        return output.getvalue()
    except Exception as e:
        print(f"[compress_image] Error: {e}")
        return None


def create_thumbnail(uploaded_file, size=(300, 300)):
    """Create thumbnail for images"""
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail(size, Image.LANCZOS)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=80, optimize=True)
        output.seek(0)

        return output.getvalue()
    except Exception as e:
        print(f"[create_thumbnail] Error: {e}")
        return None


def get_content_object(model_name, object_id):
    """Get object from model_name string like leaves.LeaveRequest"""
    if model_name not in ALLOWED_MODELS:
        return None, None

    try:
        app_label, model = model_name.split(".")
        ct = ContentType.objects.get(app_label=app_label, model=model.lower())
        obj = ct.get_object_for_this_type(id=object_id)
        return ct, obj
    except Exception as e:
        print(f"[get_content_object] Error: {e}")
        return None, None


def check_object_permission(user, obj):
    """Check if user can access this object"""
    # Employee can only access their own objects
    if hasattr(obj, "employee"):
        if hasattr(user, "employee_profile"):
            if obj.employee_id == user.employee_profile.id:
                return True

    # Managers can access company objects
    if hasattr(user, "role") and user.role in ("company_admin", "manager", "hr_manager", "super_admin"):
        if hasattr(obj, "company_id") and obj.company_id == user.company_id:
            return True
        if user.role == "super_admin":
            return True

    return False


def serialize_attachment(attachment, request=None):
    """Serialize attachment to dict"""
    base_url = ""
    if request:
        base_url = f"{request.scheme}://{request.get_host()}"

    return {
        "id": attachment.id,
        "original_name": attachment.original_name,
        "file_type": attachment.file_type,
        "file_size": attachment.file_size,
        "file_size_mb": attachment.file_size_mb,
        "mime_type": attachment.mime_type,
        "file_url": f"{base_url}{attachment.file.url}" if attachment.file else None,
        "thumbnail_url": f"{base_url}{attachment.thumbnail.url}" if attachment.thumbnail else None,
        "description": attachment.description,
        "uploaded_by": attachment.uploaded_by.username if attachment.uploaded_by else None,
        "created_at": attachment.created_at.isoformat(),
    }


# ═════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═════════════════════════════════════════════════════════════

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_attachment(request):
    """
    POST /attendance/api/mobile/attachments/upload/
    
    Body (multipart/form-data):
        - file: The file to upload
        - model: Model name (e.g., "leaves.LeaveRequest")
        - object_id: ID of the object
        - description: (optional) Description
    """
    uploaded_file = request.FILES.get("file")
    model_name = request.data.get("model")
    object_id = request.data.get("object_id")
    description = request.data.get("description", "")

    # Validate inputs
    if not uploaded_file:
        return Response({"error": "لم يتم رفع أي ملف"}, status=400)
    if not model_name or not object_id:
        return Response({"error": "model و object_id مطلوبين"}, status=400)

    # Validate file
    is_valid, error = validate_file(uploaded_file)
    if not is_valid:
        return Response({"error": error}, status=400)

    # Get content object
    content_type, obj = get_content_object(model_name, object_id)
    if not obj:
        return Response({"error": "الكائن غير موجود"}, status=404)

    # Check permission
    if not check_object_permission(request.user, obj):
        return Response({"error": "غير مصرح لك بالوصول لهذا الكائن"}, status=403)

    # Check attachment count limit
    existing_count = Attachment.all_objects.filter(
        content_type=content_type,
        object_id=object_id,
    ).count()
    if existing_count >= MAX_FILES_PER_OBJECT:
        return Response(
            {"error": f"الحد الأقصى للمرفقات {MAX_FILES_PER_OBJECT} ملفات"},
            status=400,
        )

    # Determine file type
    mime_type = uploaded_file.content_type
    file_type = get_file_type(mime_type)

    # Process file (compress if image)
    file_to_save = uploaded_file
    file_size = uploaded_file.size
    thumbnail_data = None

    if file_type == "image":
        # Create thumbnail from original
        uploaded_file.seek(0)
        thumbnail_data = create_thumbnail(uploaded_file)

        # Compress image
        uploaded_file.seek(0)
        compressed_data = compress_image(uploaded_file)
        if compressed_data:
            file_to_save = ContentFile(compressed_data, name=uploaded_file.name)
            file_size = len(compressed_data)

    # Create attachment
    try:
        attachment = Attachment(
            content_type=content_type,
            object_id=object_id,
            file=file_to_save,
            original_name=uploaded_file.name,
            file_type=file_type,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=request.user,
            description=description,
            company=obj.company if hasattr(obj, "company") else request.user.company,
        )
        attachment.save()

        # Save thumbnail
        if thumbnail_data:
            thumb_name = f"thumb_{uploaded_file.name}.jpg"
            attachment.thumbnail.save(
                thumb_name,
                ContentFile(thumbnail_data),
                save=True,
            )

        return Response({
            "success": True,
            "message": "تم رفع الملف بنجاح",
            "attachment": serialize_attachment(attachment, request),
        }, status=201)

    except Exception as e:
        return Response({"error": f"خطأ في حفظ الملف: {str(e)}"}, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_attachments(request):
    """
    GET /attendance/api/mobile/attachments/list/?model=leaves.LeaveRequest&object_id=1
    """
    model_name = request.query_params.get("model")
    object_id = request.query_params.get("object_id")

    if not model_name or not object_id:
        return Response({"error": "model و object_id مطلوبين"}, status=400)

    content_type, obj = get_content_object(model_name, object_id)
    if not obj:
        return Response({"error": "الكائن غير موجود"}, status=404)

    if not check_object_permission(request.user, obj):
        return Response({"error": "غير مصرح"}, status=403)

    attachments = Attachment.all_objects.filter(
        content_type=content_type,
        object_id=object_id,
    ).order_by("-created_at")

    return Response({
        "count": attachments.count(),
        "attachments": [serialize_attachment(a, request) for a in attachments],
    })


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_attachment(request, attachment_id):
    """
    DELETE /attendance/api/mobile/attachments/<id>/delete/
    """
    try:
        attachment = Attachment.all_objects.get(id=attachment_id)
    except Attachment.DoesNotExist:
        return Response({"error": "المرفق غير موجود"}, status=404)

    # Only uploader or admin can delete
    is_uploader = attachment.uploaded_by_id == request.user.id
    is_admin = hasattr(request.user, "role") and request.user.role in ("company_admin", "super_admin")

    if not (is_uploader or is_admin):
        return Response({"error": "غير مصرح لك بحذف هذا المرفق"}, status=403)

    # Delete files from disk
    try:
        if attachment.file:
            attachment.file.delete(save=False)
        if attachment.thumbnail:
            attachment.thumbnail.delete(save=False)
    except Exception as e:
        print(f"[delete_attachment] File delete error: {e}")

    attachment.delete()

    return Response({"success": True, "message": "تم حذف المرفق"})


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_attachment(request, attachment_id):
    """
    GET /attendance/api/mobile/attachments/<id>/download/
    """
    try:
        attachment = Attachment.all_objects.get(id=attachment_id)
    except Attachment.DoesNotExist:
        raise Http404("Attachment not found")

    # Check permission via content_object
    if attachment.content_object:
        if not check_object_permission(request.user, attachment.content_object):
            return Response({"error": "غير مصرح"}, status=403)

    try:
        response = FileResponse(
            attachment.file.open("rb"),
            as_attachment=True,
            filename=attachment.original_name,
        )
        return response
    except Exception as e:
        return Response({"error": f"خطأ في قراءة الملف: {str(e)}"}, status=500)
