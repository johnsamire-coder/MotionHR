from django.urls import path

from . import api

app_name = 'audit'

urlpatterns = [
    path('api/logs/', api.audit_logs, name='logs'),
    path('api/filters/', api.audit_filters, name='filters'),
    path('api/employee/<int:employee_id>/', api.employee_history, name='employee_history'),
]
