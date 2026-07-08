from django import forms
from .models import Employee, JobTitle
from companies.models import Branch, Department
from core.middleware import get_current_company, get_current_user


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
        
        if company:
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
    
    def clean_national_id(self):
        """التحقق من الرقم القومي"""
        national_id = self.cleaned_data.get('national_id')
        
        if national_id:
            if not national_id.isdigit():
                raise forms.ValidationError('الرقم القومي يجب أن يحتوي على أرقام فقط')
            
            if len(national_id) != 14:
                raise forms.ValidationError('الرقم القومي يجب أن يكون 14 رقم')
            
            # تحقق من عدم التكرار
            company = get_current_company()
            if company:
                qs = Employee.objects.filter(
                    company=company,
                    national_id=national_id
                )
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                
                if qs.exists():
                    raise forms.ValidationError('هذا الرقم القومي مسجل لموظف آخر')
        
        return national_id
    
    def clean_phone(self):
        """التحقق من رقم الموبايل"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # إزالة المسافات
            phone = phone.replace(' ', '').replace('-', '')
            
            if not phone.isdigit():
                raise forms.ValidationError('رقم الموبايل يجب أن يحتوي على أرقام فقط')
            
            if len(phone) < 10 or len(phone) > 15:
                raise forms.ValidationError('رقم الموبايل غير صحيح')
        
        return phone