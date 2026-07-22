# -*- coding: utf-8 -*-
"""
تصدير الصلاحيات - PDF و Excel
"""
import io
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from .permissions_models import (
    CustomRole, UserRole, UserPermissionOverride,
    PERMISSION_CHOICES, SCOPE_CHOICES
)

# ══════════════════════════════════════
# Helper: ترجمة الصلاحية والنطاق
# ══════════════════════════════════════
PERM_MAP = dict(PERMISSION_CHOICES)
SCOPE_MAP = dict(SCOPE_CHOICES)

def perm_label(code):
    return PERM_MAP.get(code, code)

def scope_label(code):
    return SCOPE_MAP.get(code, code)


# ══════════════════════════════════════
# PDF Arabic Helpers
# ══════════════════════════════════════
PDF_FONT_NAME = "CairoRegular"
PDF_FONT_PATH = Path("/var/www/motionhr/core/fonts/Cairo-Regular.ttf")

def _ensure_pdf_font():
    if PDF_FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return
    if not PDF_FONT_PATH.exists():
        raise FileNotFoundError(f"Arabic font not found: {PDF_FONT_PATH}")
    pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, str(PDF_FONT_PATH)))

def _has_arabic(text: str) -> bool:
    return any('\u0600' <= ch <= '\u06FF' for ch in text)

def pdf_text(value) -> str:
    text = str(value or '')
    if not text:
        return ''
    if _has_arabic(text):
        return get_display(arabic_reshaper.reshape(text))
    return text

def _pdf_styles():
    _ensure_pdf_font()
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title_ar",
            parent=styles["Title"],
            fontName=PDF_FONT_NAME,
            alignment=TA_CENTER,
            fontSize=16,
            leading=22,
        ),
        "heading": ParagraphStyle(
            "heading_ar",
            parent=styles["Heading2"],
            fontName=PDF_FONT_NAME,
            alignment=TA_RIGHT,
            fontSize=13,
            leading=18,
        ),
        "normal": ParagraphStyle(
            "normal_ar",
            parent=styles["Normal"],
            fontName=PDF_FONT_NAME,
            alignment=TA_RIGHT,
            fontSize=10,
            leading=16,
        ),
    }


# ══════════════════════════════════════
# Excel: دور معيّن
# ══════════════════════════════════════
def export_role_excel(role: CustomRole) -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = "صلاحيات الدور"
    ws.sheet_view.rightToLeft = True

    ws.merge_cells('A1:C1')
    ws['A1'] = f"صلاحيات الدور: {role.name} | {role.company}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.append([])
    ws.append(['الصلاحية', 'الكود', 'النطاق'])
    for cell in ws[3]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(fill_type='solid', fgColor='1a56db')
        cell.alignment = Alignment(horizontal='center')

    for perm in role.permissions.all():
        ws.append([perm_label(perm.permission), perm.permission, scope_label(perm.scope)])

    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 20

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="role_{role.id}.xlsx"'
    wb.save(response)
    return response


# ══════════════════════════════════════
# Excel: مستخدم معيّن
# ══════════════════════════════════════
def export_user_excel(user) -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = "صلاحيات المستخدم"
    ws.sheet_view.rightToLeft = True

    ws.merge_cells('A1:D1')
    ws['A1'] = f"صلاحيات: {user.get_full_name() or user.username}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.append([])
    ws.append(['المصدر', 'الدور/النوع', 'الصلاحية', 'النطاق'])
    for cell in ws[3]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(fill_type='solid', fgColor='1a56db')
        cell.alignment = Alignment(horizontal='center')

    for ur in user.custom_roles.select_related('role').all():
        for perm in ur.role.permissions.all():
            ws.append(['دور', ur.role.name, perm_label(perm.permission), scope_label(perm.scope)])

    for ov in user.permission_overrides.all():
        status = 'ممنوحة' if ov.is_granted else 'ممنوعة'
        ws.append(['استثناء شخصي', status, perm_label(ov.permission), scope_label(ov.scope)])

    for col in ['A', 'B', 'C', 'D']:
        ws.column_dimensions[col].width = 25

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="user_{user.id}_permissions.xlsx"'
    wb.save(response)
    return response


# ══════════════════════════════════════
# Excel: كل الشركة
# ══════════════════════════════════════
def export_company_excel(company) -> HttpResponse:
    wb = Workbook()

    ws1 = wb.active
    ws1.title = "الأدوار"
    ws1.sheet_view.rightToLeft = True
    ws1.append(['الدور', 'الصلاحية', 'النطاق'])
    for cell in ws1[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(fill_type='solid', fgColor='1a56db')

    for role in company.custom_roles.filter(is_active=True).prefetch_related('permissions'):
        for perm in role.permissions.all():
            ws1.append([role.name, perm_label(perm.permission), scope_label(perm.scope)])

    ws2 = wb.create_sheet("المستخدمون")
    ws2.sheet_view.rightToLeft = True
    ws2.append(['المستخدم', 'الدور المعيّن', 'الصلاحية', 'النطاق', 'مصدر'])
    for cell in ws2[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(fill_type='solid', fgColor='059669')

    for ur in UserRole.objects.filter(role__company=company).select_related('user', 'role').prefetch_related('role__permissions'):
        for perm in ur.role.permissions.all():
            ws2.append([
                ur.user.get_full_name() or ur.user.username,
                ur.role.name,
                perm_label(perm.permission),
                scope_label(perm.scope),
                'دور'
            ])

    for ov in UserPermissionOverride.objects.filter(user__company=company).select_related('user'):
        status = 'ممنوحة' if ov.is_granted else 'ممنوعة'
        ws2.append([
            ov.user.get_full_name() or ov.user.username,
            status,
            perm_label(ov.permission),
            scope_label(ov.scope),
            'استثناء شخصي'
        ])

    for ws in [ws1, ws2]:
        for col in ws.column_dimensions:
            ws.column_dimensions[col].width = 25

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="company_{company.id}_permissions.xlsx"'
    wb.save(response)
    return response


# ══════════════════════════════════════
# PDF: دور معيّن
# ══════════════════════════════════════
def export_role_pdf(role: CustomRole) -> HttpResponse:
    styles = _pdf_styles()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    elements = []

    elements.append(Paragraph(pdf_text(f"صلاحيات الدور: {role.name}"), styles["title"]))
    elements.append(Paragraph(pdf_text(f"الشركة: {role.company}"), styles["normal"]))
    elements.append(Spacer(1, 12))

    data = [[pdf_text('الصلاحية'), pdf_text('الكود'), pdf_text('النطاق')]]
    for perm in role.permissions.all():
        data.append([
            pdf_text(perm_label(perm.permission)),
            pdf_text(perm.permission),
            pdf_text(scope_label(perm.scope)),
        ])

    t = Table(data, colWidths=[200, 150, 100])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT_NAME),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a56db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(t)
    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="role_{role.id}.pdf"'
    return response


# ══════════════════════════════════════
# PDF: مستخدم معيّن
# ══════════════════════════════════════
def export_user_pdf(user) -> HttpResponse:
    styles = _pdf_styles()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    elements = []

    elements.append(Paragraph(
        pdf_text(f"صلاحيات المستخدم: {user.get_full_name() or user.username}"),
        styles["title"]
    ))
    elements.append(Spacer(1, 12))

    data = [[pdf_text('المصدر'), pdf_text('الدور'), pdf_text('الصلاحية'), pdf_text('النطاق')]]

    for ur in user.custom_roles.select_related('role').all():
        for perm in ur.role.permissions.all():
            data.append([
                pdf_text('دور'),
                pdf_text(ur.role.name),
                pdf_text(perm_label(perm.permission)),
                pdf_text(scope_label(perm.scope)),
            ])

    for ov in user.permission_overrides.all():
        status = 'ممنوحة' if ov.is_granted else 'ممنوعة'
        data.append([
            pdf_text('استثناء'),
            pdf_text(status),
            pdf_text(perm_label(ov.permission)),
            pdf_text(scope_label(ov.scope)),
        ])

    t = Table(data, colWidths=[80, 120, 180, 80])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT_NAME),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a56db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(t)
    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="user_{user.id}_permissions.pdf"'
    return response


# ══════════════════════════════════════
# PDF: كل الشركة
# ══════════════════════════════════════
def export_company_pdf(company) -> HttpResponse:
    styles = _pdf_styles()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    elements = []

    elements.append(Paragraph(pdf_text(f"صلاحيات الشركة: {company}"), styles["title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(pdf_text("الأدوار"), styles["heading"]))
    data = [[pdf_text('الدور'), pdf_text('الصلاحية'), pdf_text('النطاق')]]
    for role in company.custom_roles.filter(is_active=True).prefetch_related('permissions'):
        for perm in role.permissions.all():
            data.append([
                pdf_text(role.name),
                pdf_text(perm_label(perm.permission)),
                pdf_text(scope_label(perm.scope)),
            ])

    t = Table(data, colWidths=[150, 200, 100])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT_NAME),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a56db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(pdf_text("المستخدمون والصلاحيات"), styles["heading"]))
    data2 = [[pdf_text('المستخدم'), pdf_text('الدور'), pdf_text('الصلاحية'), pdf_text('النطاق')]]
    for ur in UserRole.objects.filter(role__company=company).select_related('user', 'role').prefetch_related('role__permissions'):
        for perm in ur.role.permissions.all():
            data2.append([
                pdf_text(ur.user.get_full_name() or ur.user.username),
                pdf_text(ur.role.name),
                pdf_text(perm_label(perm.permission)),
                pdf_text(scope_label(perm.scope)),
            ])

    t2 = Table(data2, colWidths=[120, 120, 160, 80])
    t2.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT_NAME),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(t2)
    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="company_{company.id}_permissions.pdf"'
    return response
