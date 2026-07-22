# -*- coding: utf-8 -*-
"""
تصدير الصلاحيات - PDF و Excel
"""
import io
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
from .permissions_models import CustomRole, UserRole, UserPermissionOverride, PERMISSION_CHOICES, SCOPE_CHOICES

# ══════════════════════════════════════
# Helper: ترجمة الصلاحية والنطاق
# ══════════════════════════════════════
PERM_MAP = dict(PERMISSION_CHOICES)
SCOPE_MAP = dict(SCOPE_CHOICES)

def perm_label(code): return PERM_MAP.get(code, code)
def scope_label(code): return SCOPE_MAP.get(code, code)


# ══════════════════════════════════════
# Excel: دور معيّن
# ══════════════════════════════════════
def export_role_excel(role: CustomRole) -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = "صلاحيات الدور"
    ws.sheet_view.rightToLeft = True

    # Header
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

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
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

    # صلاحيات من الأدوار
    for ur in user.custom_roles.select_related('role').all():
        for perm in ur.role.permissions.all():
            ws.append(['دور', ur.role.name, perm_label(perm.permission), scope_label(perm.scope)])

    # استثناءات شخصية
    for ov in user.permission_overrides.all():
        status = '✅ ممنوحة' if ov.is_granted else '❌ ممنوعة'
        ws.append(['استثناء شخصي', status, perm_label(ov.permission), scope_label(ov.scope)])

    for col in ['A','B','C','D']:
        ws.column_dimensions[col].width = 25

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="user_{user.id}_permissions.xlsx"'
    wb.save(response)
    return response


# ══════════════════════════════════════
# Excel: كل الشركة
# ══════════════════════════════════════
def export_company_excel(company) -> HttpResponse:
    wb = Workbook()

    # شيت الأدوار
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

    # شيت المستخدمين
    ws2 = wb.create_sheet("المستخدمون")
    ws2.sheet_view.rightToLeft = True
    ws2.append(['المستخدم', 'الدور المعيّن', 'الصلاحية', 'النطاق', 'مصدر'])
    for cell in ws2[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(fill_type='solid', fgColor='059669')

    for ur in UserRole.objects.filter(role__company=company).select_related('user','role').prefetch_related('role__permissions'):
        for perm in ur.role.permissions.all():
            ws2.append([
                ur.user.get_full_name() or ur.user.username,
                ur.role.name,
                perm_label(perm.permission),
                scope_label(perm.scope),
                'دور'
            ])

    for ov in UserPermissionOverride.objects.filter(user__company=company).select_related('user'):
        status = '✅ ممنوحة' if ov.is_granted else '❌ ممنوعة'
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

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="company_{company.id}_permissions.xlsx"'
    wb.save(response)
    return response


# ══════════════════════════════════════
# PDF: دور معيّن
# ══════════════════════════════════════
def export_role_pdf(role: CustomRole) -> HttpResponse:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('title', parent=styles['Title'], alignment=TA_CENTER, fontSize=16)
    elements.append(Paragraph(f"صلاحيات الدور: {role.name}", title_style))
    elements.append(Paragraph(f"الشركة: {role.company}", styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [['الصلاحية', 'الكود', 'النطاق']]
    for perm in role.permissions.all():
        data.append([perm_label(perm.permission), perm.permission, scope_label(perm.scope)])

    t = Table(data, colWidths=[200, 150, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a56db')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(t)
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="role_{role.id}.pdf"'
    return response


# ══════════════════════════════════════
# PDF: مستخدم معيّن
# ══════════════════════════════════════
def export_user_pdf(user) -> HttpResponse:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('title', parent=styles['Title'], alignment=TA_CENTER, fontSize=16)
    elements.append(Paragraph(f"صلاحيات المستخدم: {user.get_full_name() or user.username}", title_style))
    elements.append(Spacer(1, 12))

    data = [['المصدر', 'الدور', 'الصلاحية', 'النطاق']]
    for ur in user.custom_roles.select_related('role').all():
        for perm in ur.role.permissions.all():
            data.append(['دور', ur.role.name, perm_label(perm.permission), scope_label(perm.scope)])
    for ov in user.permission_overrides.all():
        status = '✅' if ov.is_granted else '❌'
        data.append(['استثناء', status, perm_label(ov.permission), scope_label(ov.scope)])

    t = Table(data, colWidths=[80, 120, 180, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a56db')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(t)
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="user_{user.id}_permissions.pdf"'
    return response


# ══════════════════════════════════════
# PDF: كل الشركة
# ══════════════════════════════════════
def export_company_pdf(company) -> HttpResponse:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('title', parent=styles['Title'], alignment=TA_CENTER, fontSize=16)
    elements.append(Paragraph(f"صلاحيات الشركة: {company}", title_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("الأدوار", styles['Heading2']))
    data = [['الدور', 'الصلاحية', 'النطاق']]
    for role in company.custom_roles.filter(is_active=True).prefetch_related('permissions'):
        for perm in role.permissions.all():
            data.append([role.name, perm_label(perm.permission), scope_label(perm.scope)])

    t = Table(data, colWidths=[150, 200, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a56db')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("المستخدمون والصلاحيات", styles['Heading2']))
    data2 = [['المستخدم', 'الدور', 'الصلاحية', 'النطاق']]
    for ur in UserRole.objects.filter(role__company=company).select_related('user','role').prefetch_related('role__permissions'):
        for perm in ur.role.permissions.all():
            data2.append([
                ur.user.get_full_name() or ur.user.username,
                ur.role.name,
                perm_label(perm.permission),
                scope_label(perm.scope),
            ])

    t2 = Table(data2, colWidths=[120, 120, 160, 80])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(t2)
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="company_{company.id}_permissions.pdf"'
    return response
