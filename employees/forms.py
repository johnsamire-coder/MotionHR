from django import forms
from .models import Employee, JobTitle
from companies.models import Branch, Department
from core.middleware import get_current_company, get_current_user
import datetime


class EmployeeForm(forms.ModelForm):
    """فورم إضافة وتعديل الموظف"""
    
    class Meta:
        model = Employee
        exclude = [
            'company', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'user'
        ]
        widgets = {
            # البيانات الأساسية
            'employee_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'يُترك فارغاً للتوليد التلقائي'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            
            # البيانات الشخصية
            'first_name_ar': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'مثال: أحمد'
            }),
            'middle_name_ar': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'مثال: محمد'
            }),
            'last_name_ar': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'مثال: علي'
            }),
            'first_name_en': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ahmed'
            }),
            'last_name_en': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ali'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '14 رقم',
                'maxlength': '14'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'religion': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            
            # التواصل
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'example@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '01xxxxxxxxx'
            }),
            'phone2': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '01xxxxxxxxx'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            
            # التعيين
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'contract_end_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'job_title': forms.Select(attrs={'class': 'form-select'}),
            'direct_manager': forms.Select(attrs={'class': 'form-select'}),
            
            # الراتب
            'basic_salary': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            
            # البنك
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account': forms.TextInput(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            
            # التأمينات
            'insurance_number': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'has_insurance': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            # الطوارئ
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: الوالد، الأخ، الزوجة'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            
            # الحالة
            'status': forms.Select(attrs={'class': 'form-select'}),
            'termination_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'termination_reason': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
            
            # التتبع
            'is_field_worker': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # فلترة القوائم حسب الشركة الحالية
        company = get_current_company()
        user = get_current_user()
        
        # لو Super Admin يشوف كل حاجة
        if user and hasattr(user, 'role') and user.role == 'super_admin':
            self.fields['branch'].queryset = Branch.objects.all()
            self.fields['department'].queryset = Department.objects.all()
            self.fields['job_title'].queryset = JobTitle.all_objects.all()
            self.fields['direct_manager'].queryset = Employee.all_objects.all()
        elif company:
            self.fields['branch'].queryset = Branch.objects.filter(company=company)
            self.fields['department'].queryset = Department.objects.filter(company=company)
            self.fields['job_title'].queryset = JobTitle.objects.filter(company=company)
            self.fields['direct_manager'].queryset = Employee.objects.filter(company=company)
        
        # employee_code مش مطلوب
        self.fields['employee_code'].required = False
        
        # حقول اختيارية
        optional_fields = [
            'middle_name_ar', 'first_name_en', 'last_name_en',
            'religion', 'phone2', 'address', 'city', 'email',
            'photo', 'contract_end_date', 'direct_manager',
            'bank_name', 'bank_account', 'iban',
            'insurance_number', 'insurance_date',
            'emergency_contact_name', 'emergency_contact_relation',
            'emergency_contact_phone', 'termination_date',
            'termination_reason', 'notes'
        ]
        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email

        email = email.strip().lower()
        company = get_current_company()

        if company:
            qs = Employee.objects.filter(company=company, email__iexact=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    'هذا البريد الالكتروني مسجل لموظف اخر في نفس الشركة'
                )

        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_qs = User.objects.filter(email__iexact=email)
        if self.instance.pk and getattr(self.instance, 'user', None):
            user_qs = user_qs.exclude(pk=self.instance.user.pk)
        if user_qs.exists():
            raise forms.ValidationError(
                'هذا البريد الالكتروني مستخدم بالفعل في النظام'
            )

        return email

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if not birth_date:
            return birth_date

        today = datetime.date.today()

        if birth_date > today:
            raise forms.ValidationError(
                'تاريخ الميلاد لا يمكن ان يكون في المستقبل'
            )

        try:
            min_date = today.replace(year=today.year - 100)
        except ValueError:
            min_date = today.replace(year=today.year - 100, day=28)

        if birth_date < min_date:
            raise forms.ValidationError(
                'تاريخ الميلاد غير صحيح - يتجاوز 100 سنة'
            )

        try:
            max_date = today.replace(year=today.year - 16)
        except ValueError:
            max_date = today.replace(year=today.year - 16, day=28)

        if birth_date > max_date:
            raise forms.ValidationError(
                'يجب ان يكون عمر الموظف 16 سنة على الاقل'
            )

        return birth_date

    def clean_hire_date(self):
        hire_date = self.cleaned_data.get('hire_date')
        if not hire_date:
            return hire_date

        today = datetime.date.today()

        try:
            min_date = today.replace(year=today.year - 50)
        except ValueError:
            min_date = today.replace(year=today.year - 50, day=28)

        if hire_date < min_date:
            raise forms.ValidationError(
                'تاريخ التعيين غير صحيح - يتجاوز 50 سنة'
            )

        return hire_date

    def clean_national_id(self):
        national_id = self.cleaned_data.get('national_id')

        if not national_id:
            return national_id

        if not national_id.isdigit():
            raise forms.ValidationError('الرقم القومي يجب ان يحتوي على ارقام فقط (14 رقم)')

        if len(national_id) != 14:
            raise forms.ValidationError(
                'الرقم القومي يجب ان يكون 14 رقم - ادخلت %d رقم' % len(national_id)
            )

        if national_id[0] not in ('2', '3'):
            raise forms.ValidationError('الرقم القومي غير صحيح - يجب ان يبدا بـ 2 او 3')

        company = get_current_company()
        if company:
            qs = Employee.objects.filter(
                company=company,
                national_id=national_id
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError('هذا الرقم القومي مسجل لموظف اخر في نفس الشركة')

        return national_id

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        if not phone:
            return phone

        phone = phone.replace(' ', '').replace('-', '')

        if not phone.isdigit():
            raise forms.ValidationError('رقم الموبايل يجب ان يحتوي على ارقام فقط')

        if len(phone) < 10 or len(phone) > 15:
            raise forms.ValidationError('رقم الموبايل غير صحيح - يجب ان يكون بين 10 و 15 رقم')

        return phone

    def clean(self):
        cleaned_data = super().clean()
        birth_date = cleaned_data.get('birth_date')
        hire_date = cleaned_data.get('hire_date')
        contract_end_date = cleaned_data.get('contract_end_date')

        if birth_date and hire_date:
            if hire_date <= birth_date:
                self.add_error(
                    'hire_date',
                    'تاريخ التعيين يجب ان يكون بعد تاريخ الميلاد'
                )

        if hire_date and contract_end_date:
            if contract_end_date <= hire_date:
                self.add_error(
                    'contract_end_date',
                    'تاريخ انتهاء العقد يجب ان يكون بعد تاريخ التعيين'
                )

        return cleaned_data
