from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("",           views.reports_home,      name="home"),
    path("attendance/",views.attendance_report,  name="attendance"),
    path("late/",      views.late_report,        name="late"),
    path("leaves/",    views.leave_report,       name="leaves"),
    path("field/",     views.field_report,       name="field"),
    path("employees/", views.employees_report,   name="employees"),
]
