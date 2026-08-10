"""
MotionHR - Trial Signup API
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from companies.models import Company
from employees.models import Employee, Branch, Department, JobTitle
from core.username_generator import generate_owner_username
from subscriptions.models import SubscriptionPlan, CompanySubscription

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def trial_signup(request):
    """
    Signup لتجربة مجانية
    
    Body:
    {
        "company_name": "اسم الشركة",
        "owner_name": "اسم صاحب الشركة",
        "email": "test@example.com",
        "phone": "01001234567",
        "password": "12345678",
        "industry": "construction" (optional),
        "city": "القاهرة" (optional)
    }
    """
    data = request.data
    
    # ── Validation ──────────────────────────────
    required = ['company_name', 'owner_name', 'email', 'phone', 'password']
    for field in required:
        if not data.get(field):
            return Response({
                'success': False,
                'error': f'حقل {field} مطلوب'
            }, status=400)
    
    company_name = data['company_name'].strip()
    owner_name = data['owner_name'].strip()
    email = data['email'].strip().lower()
    phone = data['phone'].strip()
    password = data['password']
    
    # Password validation
    if len(password) < 6:
        return Response({
            'success': False,
            'error': 'كلمة السر يجب أن تكون 6 حروف على الأقل'
        }, status=400)
    
    # Check email/phone unique
    if User.objects.filter(email=email).exists():
        return Response({
            'success': False,
            'error': 'الإيميل مسجل بالفعل'
        }, status=400)
    
    if User.objects.filter(phone=phone).exists():
        return Response({
            'success': False,
            'error': 'رقم الهاتف مسجل بالفعل'
        }, status=400)
    
    # ── Get Trial Plan ──────────────────────────
    trial_plan = SubscriptionPlan.objects.filter(is_trial=True, is_active=True).first()
    if not trial_plan:
        return Response({
            'success': False,
            'error': 'خطة التجربة غير متاحة حالياً'
        }, status=500)
    
    # ── Create Everything (Transaction) ─────────
    try:
        with transaction.atomic():
            # 1. Create Company
            company = Company.objects.create(
                name_ar=company_name,
                name_en=company_name,
                email=email,
                phone=phone,
                is_active=True,
            )
            
            # 2. Generate username: admin_{first_name}
            name_parts_for_uname = owner_name.strip().split()
            first_for_uname = name_parts_for_uname[0] if name_parts_for_uname else 'owner'
            username = generate_owner_username(first_for_uname, User=User)
            
            # 3. Create Owner User
            name_parts = owner_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role='company_admin',
                company=company,
            )
            
            # 4. Create default Branch, Department, JobTitle if not exists
            branch = Branch._base_manager.filter(company=company, is_main=True).first()
            if not branch:
                branch = Branch._base_manager.filter(company=company).first()
            if not branch:
                branch = Branch._base_manager.create(
                    company=company,
                    name_ar='الفرع الرئيسي',
                    name_en='Main Branch',
                    is_main=True,
                )

            department = Department._base_manager.filter(company=company).first()
            if not department:
                department = Department._base_manager.create(
                    company=company,
                    name_ar='الإدارة العامة',
                    name_en='General Management',
                )

            job_title = JobTitle._base_manager.filter(company=company).first()
            if not job_title:
                job_title = JobTitle._base_manager.create(
                    company=company,
                    name_ar='صاحب الشركة',
                    name_en='Owner',
                )

            owner_national_id = str(data.get("national_id", "")).strip() or f"00000000000{company.id:03d}"[-14:]
            owner_birth_date = data.get("birth_date") or timezone.now().date().replace(year=timezone.now().year - 30)
            owner_gender = str(data.get("gender", "male")).strip().lower()
            if owner_gender not in ("male", "female"):
                owner_gender = "male"

            Employee._base_manager.create(
                    company=company,
                    user=user,
                    first_name_ar=first_name or owner_name,
                    last_name_ar=last_name or "صاحب الشركة",
                    first_name_en=first_name or owner_name,
                    last_name_en=last_name or "Owner",
                    national_id=owner_national_id,
                    birth_date=owner_birth_date,
                    gender=owner_gender,
                    phone=phone,
                    email=email,
                    hire_date=timezone.now().date(),
                    branch=branch,
                    department=department,
                    job_title=job_title,
                    basic_salary=0,
                    marital_status="single",
                    contract_type="permanent",
                    salary_payment_method="cash",
                    worker_type="office",
                    status="active",
                )

            # 5. Create Subscription
            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=trial_plan.trial_days)
            
            subscription = CompanySubscription.objects.create(
                company=company,
                plan=trial_plan,
                start_date=start_date,
                end_date=end_date,
                trial_end_date=end_date,
                is_trial=True,
                status='trial',
                activated_at=timezone.now(),
            )
            
            # 5. Create Auth Token
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                'success': True,
                'message': f'تم إنشاء حسابك بنجاح! لديك {trial_plan.trial_days} يوم تجربة مجانية.',
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': username,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'company_admin',
                },
                'company': {
                    'id': company.id,
                    'name_ar': company.name_ar,
                },
                'subscription': {
                    'plan': trial_plan.name_ar,
                    'trial_end_date': str(end_date),
                    'days_remaining': trial_plan.trial_days,
                    'max_employees': trial_plan.max_employees,
                },
            }, status=201)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'خطأ في إنشاء الحساب: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def subscription_status(request):
    """
    يرجع حالة اشتراك الشركة الحالية
    """
    from rest_framework.authentication import TokenAuthentication
    from rest_framework_simplejwt.authentication import JWTAuthentication
    
    # جرب auth manual
    user = None
    for AuthClass in [TokenAuthentication, JWTAuthentication]:
        try:
            auth_result = AuthClass().authenticate(request)
            if auth_result:
                user = auth_result[0]
                break
        except Exception:
            continue
    
    if not user or not user.is_authenticated:
        return Response({'success': False, 'error': 'Unauthorized'}, status=401)
    
    company = getattr(user, 'company', None)
    if not company:
        return Response({'success': False, 'error': 'No company'}, status=400)
    
    try:
        sub = CompanySubscription.objects.filter(company=company).select_related('plan').first()
        if not sub:
            return Response({'success': True, 'has_subscription': False}, status=200)
        
        # عدد الموظفين الحاليين
        from employees.models import Employee
        current_employees = Employee._base_manager.filter(company=company, status='active').count()
        max_employees = sub.custom_max_employees or sub.plan.max_employees
        
        return Response({
            'success': True,
            'has_subscription': True,
            'is_trial': sub.is_trial,
            'plan_name': sub.plan.name_ar,
            'status': sub.status,
            'days_remaining': sub.days_remaining,
            'trial_end_date': str(sub.trial_end_date) if sub.trial_end_date else None,
            'end_date': str(sub.end_date),
            'current_employees': current_employees,
            'max_employees': max_employees,
            'employees_percentage': round((current_employees / max_employees * 100) if max_employees > 0 else 0, 1),
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
