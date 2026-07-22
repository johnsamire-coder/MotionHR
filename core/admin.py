from .models import TrialSignupLead
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
import csv


@admin.register(TrialSignupLead)
class TrialSignupLeadAdmin(admin.ModelAdmin):
    list_display = (
        'company_name',
        'contact_name',
        'whatsapp_link',
        'phone',
        'email',
        'employees_count',
        'status_badge',
        'trial_days_left',
        'created_at',
    )
    list_filter = ('status', 'industry', 'created_at', 'trial_end_date')
    search_fields = ('company_name', 'contact_name', 'phone', 'whatsapp', 'email')
    ordering = ('-created_at',)
    readonly_fields = (
        'generated_username', 'generated_password',
        'created_company', 'created_user',
        'trial_start_date', 'trial_end_date',
        'created_at', 'updated_at',
    )

    fieldsets = (
        ('بيانات العميل', {
            'fields': ('company_name', 'contact_name', 'phone', 'whatsapp', 'email',
                       'employees_count', 'city', 'industry', 'notes'),
        }),
        ('حالة الطلب', {
            'fields': ('status', 'source'),
        }),
        ('التجربة المجانية', {
            'fields': ('trial_start_date', 'trial_end_date',
                       'generated_username', 'generated_password',
                       'created_company', 'created_user'),
            'classes': ('collapse',),
        }),
        ('التتبع', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['export_to_csv', 'mark_as_contacted', 'mark_as_converted']

    def whatsapp_link(self, obj):
        """زرار WhatsApp Quick Action"""
        if not obj.whatsapp:
            return '-'
        # ننظف الرقم من الرموز
        clean_number = ''.join(filter(str.isdigit, obj.whatsapp))
        # نضيف كود مصر لو مش موجود
        if clean_number.startswith('0'):
            clean_number = '2' + clean_number
        elif not clean_number.startswith('20'):
            clean_number = '20' + clean_number

        message = f"مرحباً {obj.contact_name}، تواصلنا معك بخصوص طلبك على MotionHR"
        # نعمل URL encode للرسالة
        import urllib.parse
        encoded_msg = urllib.parse.quote(message)

        url = f"https://wa.me/{clean_number}?text={encoded_msg}"
        return format_html(
            '<a href="{}" target="_blank" style="background:#25D366;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:700;">💬 واتساب</a>',
            url
        )
    whatsapp_link.short_description = 'WhatsApp'

    def status_badge(self, obj):
        """حالة الطلب بألوان"""
        colors = {
            'new': '#3B82F6',
            'activated': '#10B981',
            'contacted': '#F59E0B',
            'converted': '#059669',
            'expired': '#6B7280',
            'rejected': '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background:{};color:white;padding:4px 10px;border-radius:4px;font-weight:600;font-size:0.85em;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'

    def trial_days_left(self, obj):
        """الأيام المتبقية للتجربة"""
        if not obj.trial_end_date:
            return '-'
        from datetime import date
        days = (obj.trial_end_date - date.today()).days
        if days < 0:
            return format_html('<span style="color:#EF4444;">انتهت</span>')
        elif days == 0:
            return format_html('<span style="color:#F59E0B;font-weight:700;">اليوم</span>')
        elif days <= 3:
            return format_html('<span style="color:#F59E0B;font-weight:700;">{} أيام</span>', days)
        else:
            return format_html('<span style="color:#10B981;">{} يوم</span>', days)
    trial_days_left.short_description = 'الأيام المتبقية'

    def export_to_csv(self, request, queryset):
        """تصدير الطلبات المحددة كـ Excel/CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="motionhr_leads.csv"'
        response.write('\ufeff')  # BOM for Excel Arabic support

        writer = csv.writer(response)
        writer.writerow([
            'اسم الشركة', 'اسم المسؤول', 'الموبايل', 'الواتساب',
            'الإيميل', 'عدد الموظفين', 'المدينة', 'الصناعة',
            'الحالة', 'تاريخ التسجيل', 'الأيام المتبقية', 'ملاحظات'
        ])

        from datetime import date
        for obj in queryset:
            days_left = ''
            if obj.trial_end_date:
                d = (obj.trial_end_date - date.today()).days
                days_left = f"{d}" if d >= 0 else "منتهية"

            writer.writerow([
                obj.company_name,
                obj.contact_name,
                obj.phone,
                obj.whatsapp,
                obj.email,
                obj.employees_count,
                obj.city or '-',
                obj.industry or '-',
                obj.get_status_display(),
                obj.created_at.strftime('%Y-%m-%d %H:%M'),
                days_left,
                obj.notes or '-',
            ])

        self.message_user(request, f'✅ تم تصدير {queryset.count()} طلب')
        return response
    export_to_csv.short_description = '📥 تصدير المحدد كـ Excel'

    def mark_as_contacted(self, request, queryset):
        """تحديد الطلبات كتم التواصل"""
        count = queryset.update(status='contacted')
        self.message_user(request, f'✅ تم تحديث {count} طلب كـ "تم التواصل"')
    mark_as_contacted.short_description = '☎️ تحديد كـ "تم التواصل"'

    def mark_as_converted(self, request, queryset):
        """تحديد الطلبات كعميل"""
        count = queryset.update(status='converted')
        self.message_user(request, f'🎉 تم تحويل {count} طلب لعميل')
    mark_as_converted.short_description = '🎉 تحويل لعميل'
