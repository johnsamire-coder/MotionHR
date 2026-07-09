from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
import csv
from datetime import datetime

from .models import Employee, JobTitle
from .forms import EmployeeForm
from companies.models import Branch, Department
from core.permissions import (
    get_accessible_employees,
    can_user_edit_employee,
    can_user_delete_employee,
    can_user_add_employee,
    is_admin_or_hr,
)


@login_required
def employee_list(request):
    """قائمة الموظفين - محكومة بالصلاحيات الهرمية"""
    
    # جلب الموظفين المسموح رؤيتهم
    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title'
    )
    
    # البحث
    search = request.GET.get('search', '').strip()
    if search:
        employees = employees.filter(
            Q(employee_code__icontains=search) |
            Q(first_name_ar__icontains=search) |
            Q(last_name_ar__icontains=search) |
            Q(national_id__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    
    # الفلترة
    status_filter = request.GET.get('status', '')
    if status_filter:
        employees = employees.filter(status=status_filter)
    
    branch_filter = request.GET.get('branch', '')
    if branch_filter:
        employees = employees.filter(branch_id=branch_filter)
    
    department_filter = request.GET.get('department', '')
    if department_filter:
        employees = employees.filter(department_id=department_filter)
    
    # التصدير
    export_type = request.GET.get('export', '')
    if export_type == 'excel':
        return export_employees_excel(employees)
    elif export_type == 'pdf':
        try:
            return export_employees_pdf(employees)
        except Exception as e:
            messages.warning(request, f'PDF غير متاح - جرب Excel')
            return redirect('employees:list')
    
    # Pagination
    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    branches = Branch.objects.all()
    departments = Department.objects.all()
    
    context = {
        'page_obj': page_obj,
        'employees': page_obj.object_list,
        'total_count': paginator.count,
        'search': search,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'department_filter': department_filter,
        'branches': branches,
        'departments': departments,
        'status_choices': Employee.STATUS_CHOICES,
        'can_add': can_user_add_employee(request.user),
        'is_admin_hr': is_admin_or_hr(request.user),
    }
    
    return render(request, 'employees/list.html', context)


def export_employees_excel(employees):
    """تصدير Excel"""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f"employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow([
        'الرقم الوظيفي', 'الاسم بالعربي', 'الاسم بالإنجليزي',
        'الرقم القومي', 'تاريخ الميلاد', 'النوع', 'رقم الموبايل',
        'البريد الإلكتروني', 'الفرع', 'الإدارة', 'المسمى الوظيفي',
        'تاريخ التعيين', 'الراتب الأساسي', 'الحالة', 'موظف ميداني',
    ])
    
    for emp in employees:
        writer.writerow([
            emp.employee_code, emp.full_name_ar, emp.full_name_en or '',
            emp.national_id, emp.birth_date, emp.get_gender_display(),
            emp.phone, emp.email or '', emp.branch.name_ar,
            emp.department.name_ar, emp.job_title.name_ar,
            emp.hire_date, emp.basic_salary, emp.get_status_display(),
            'نعم' if emp.is_field_worker else 'لا',
        ])
    
    return response


def export_employees_pdf(employees):
    """تصدير PDF"""
    from django.template.loader import render_to_string
    from weasyprint import HTML
    from django.utils import timezone
    
    html_string = render_to_string('employees/print_list.html', {
        'employees': employees,
        'generated_at': timezone.now(),
        'total_count': employees.count() if hasattr(employees, 'count') else len(employees),
    })
    
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def employee_add(request):
    """إضافة موظف جديد - Admin/HR فقط"""
    
    if not can_user_add_employee(request.user):
        raise PermissionDenied('ليس لديك صلاحية لإضافة موظفين')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            messages.success(
                request,
                f'تم إضافة الموظف {employee.full_name_ar} بنجاح ✅'
            )
            return redirect('employees:detail', pk=employee.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = EmployeeForm()
    
    context = {
        'form': form,
        'title': 'إضافة موظف جديد',
        'is_edit': False,
    }
    
    return render(request, 'employees/form.html', context)


@login_required
def employee_detail(request, pk):
    """تفاصيل الموظف - محكومة بالصلاحيات"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # التحقق من الصلاحية
    accessible = get_accessible_employees(request.user)
    if not accessible.filter(pk=pk).exists():
        raise PermissionDenied('ليس لديك صلاحية لعرض هذا الموظف')
    
    context = {
        'employee': employee,
        'can_edit': can_user_edit_employee(request.user, employee),
        'can_delete': can_user_delete_employee(request.user, employee),
    }
    
    return render(request, 'employees/detail.html', context)


@login_required
def employee_edit(request, pk):
    """تعديل الموظف - محكومة بالصلاحيات"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # التحقق من الصلاحية
    if not can_user_edit_employee(request.user, employee):
        raise PermissionDenied('ليس لديك صلاحية لتعديل هذا الموظف')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(
                request,
                f'تم تحديث بيانات {employee.full_name_ar} بنجاح ✅'
            )
            return redirect('employees:detail', pk=employee.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = EmployeeForm(instance=employee)
    
    context = {
        'form': form,
        'employee': employee,
        'title': f'تعديل بيانات {employee.full_name_ar}',
        'is_edit': True,
    }
    
    return render(request, 'employees/form.html', context)


@login_required
def employee_delete(request, pk):
    """حذف الموظف - Admin فقط"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if not can_user_delete_employee(request.user, employee):
        raise PermissionDenied('ليس لديك صلاحية لحذف هذا الموظف')
    
    if request.method == 'POST':
        name = employee.full_name_ar
        employee.delete()
        messages.success(request, f'تم حذف الموظف {name} بنجاح')
        return redirect('employees:list')
    
    return render(request, 'employees/delete_confirm.html', {'employee': employee})


@login_required
def employee_print(request, pk=None):
    """صفحة طباعة"""
    from django.utils import timezone
    
    if pk:
        employee = get_object_or_404(Employee, pk=pk)
        accessible = get_accessible_employees(request.user)
        if not accessible.filter(pk=pk).exists():
            raise PermissionDenied('ليس لديك صلاحية')
        employees = accessible.filter(pk=pk)
        title = f"بيانات {employee.full_name_ar}"
    else:
        employees = get_accessible_employees(request.user).select_related(
            'branch', 'department', 'job_title'
        )
        title = "قائمة الموظفين"
    
    context = {
        'employees': employees,
        'title': title,
        'generated_at': timezone.now(),
        'is_single': pk is not None,
    }
    
    return render(request, 'employees/print_list.html', context)


@login_required
def employee_print_detail(request, pk):
    """طباعة بيانات موظف"""
    from django.utils import timezone
    
    employee = get_object_or_404(Employee, pk=pk)
    accessible = get_accessible_employees(request.user)
    if not accessible.filter(pk=pk).exists():
        raise PermissionDenied('ليس لديك صلاحية')
    
    context = {
        'employee': employee,
        'generated_at': timezone.now(),
    }
    
    return render(request, 'employees/print_detail.html', context)
