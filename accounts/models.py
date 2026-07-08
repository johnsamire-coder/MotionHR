from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('company_admin', 'مدير الشركة'),
        ('hr_manager', 'مدير الموارد البشرية'),
        ('manager', 'مدير'),
        ('employee', 'موظف'),
    ]
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الموبايل'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee',
        verbose_name='الدور'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='users',
        verbose_name='الشركة'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='الصورة الشخصية'
    )
    
    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"