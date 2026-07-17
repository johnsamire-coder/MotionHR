from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


def _name_of(obj):
    if not obj:
        return None
    return getattr(obj, "name_ar", None) or getattr(obj, "name", None) or str(obj)


def _serialize_employee(emp):
    manager = None
    if emp.direct_manager:
        manager = {
            "id": emp.direct_manager.id,
            "name": getattr(emp.direct_manager, "full_name_ar", None) or str(emp.direct_manager),
        }
    parts = [emp.first_name_ar or "", emp.middle_name_ar or "", emp.last_name_ar or ""]
    full_ar = " ".join([p for p in parts if p]).strip()
    parts_en = [emp.first_name_en or "", emp.last_name_en or ""]
    full_en = " ".join([p for p in parts_en if p]).strip()
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "photo": emp.photo.url if emp.photo else None,
        "full_name_ar": full_ar,
        "full_name_en": full_en,
        "national_id": emp.national_id,
        "birth_date": str(emp.birth_date) if emp.birth_date else None,
        "gender": emp.get_gender_display() if emp.gender else None,
        "marital_status": emp.get_marital_status_display() if emp.marital_status else None,
        "religion": emp.get_religion_display() if emp.religion else None,
        "nationality": emp.nationality,
        "email": emp.email,
        "phone": emp.phone,
        "phone2": emp.phone2,
        "address": emp.address,
        "city": emp.city,
        "hire_date": str(emp.hire_date) if emp.hire_date else None,
        "contract_type": emp.get_contract_type_display() if emp.contract_type else None,
        "contract_end_date": str(emp.contract_end_date) if emp.contract_end_date else None,
        "branch": _name_of(emp.branch),
        "department": _name_of(emp.department),
        "job_title": _name_of(emp.job_title),
        "direct_manager": manager,
        "basic_salary": float(emp.basic_salary or 0),
        "bank_name": emp.bank_name,
        "bank_account": emp.bank_account,
        "iban": emp.iban,
        "status": emp.get_status_display() if hasattr(emp, "get_status_display") else None,
    }


def _serialize_document(doc):
    today = date.today()
    return {
        "id": doc.id,
        "document_type": doc.get_document_type_display(),
        "document_type_code": doc.document_type,
        "title": doc.title,
        "file_url": doc.file.url if doc.file else None,
        "issue_date": str(doc.issue_date) if doc.issue_date else None,
        "expiry_date": str(doc.expiry_date) if doc.expiry_date else None,
        "is_expired": bool(doc.expiry_date and doc.expiry_date < today),
        "expires_soon": bool(doc.expiry_date and today <= doc.expiry_date <= today + timedelta(days=30)),
        "notes": doc.notes,
    }


def _serialize_movement(mv):
    return {
        "id": mv.id,
        "type": mv.get_movement_type_display() if hasattr(mv, "get_movement_type_display") else mv.movement_type,
        "type_code": mv.movement_type,
        "date": str(getattr(mv, "movement_date", None) or getattr(mv, "created_at", "")),
        "notes": getattr(mv, "notes", None) or getattr(mv, "description", None) or "",
    }


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_profile(request):
    try:
        emp = getattr(request.user, "employee_profile", None)
        if not emp:
            return Response({"error": "no employee profile"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_serialize_employee(emp))
    except Exception as e:
        logger.exception("my_profile error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_documents(request):
    try:
        emp = getattr(request.user, "employee_profile", None)
        if not emp:
            return Response({"documents": []})
        docs = emp.documents.all().order_by("-created_at")
        return Response({"documents": [_serialize_document(d) for d in docs]})
    except Exception as e:
        logger.exception("my_documents error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_movements(request):
    try:
        emp = getattr(request.user, "employee_profile", None)
        if not emp:
            return Response({"movements": []})
        moves = emp.movements.all().order_by("-created_at")[:50]
        return Response({"movements": [_serialize_movement(m) for m in moves]})
    except Exception as e:
        logger.exception("my_movements error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
