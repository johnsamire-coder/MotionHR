"""
URLs للتقارير الجديدة + الـ Export الموحد
ملف مستقل عشان نتجنب أي conflict
"""
from django.urls import path
from attendance.api_reports import (
    executive_dashboard,
    turnover_report,
    branch_comparison_report,
    bank_transfer_report,
    insurance_report,
    tax_report,
    loans_advances_report,
    eos_report,
    reimbursements_report,
    contracts_expiry_report,
    missions_performance_report,
    unified_report_export,
)

urlpatterns = [
    path('executive-dashboard/', executive_dashboard),
    path('turnover/', turnover_report),
    path('branch-comparison/', branch_comparison_report),
    path('bank-transfer/', bank_transfer_report),
    path('insurance/', insurance_report),
    path('tax/', tax_report),
    path('loans-advances/', loans_advances_report),
    path('eos/', eos_report),
    path('reimbursements/', reimbursements_report),
    path('contracts-expiry/', contracts_expiry_report),
    path('missions-performance/', missions_performance_report),
    path('unified-export/', unified_report_export),
]
