from django.urls import path
from . import views

app_name = "leaves"

urlpatterns = [

    # أنواع الإجازات
    path("types/",
         views.leave_types_list, name="leave_types_list"),
    path("types/add/",
         views.leave_type_add, name="leave_type_add"),
    path("types/<int:pk>/edit/",
         views.leave_type_edit, name="leave_type_edit"),
    path("types/<int:pk>/delete/",
         views.leave_type_delete, name="leave_type_delete"),

    # الطلبات
    path("",
         views.leave_requests_list, name="leave_requests_list"),
    path("add/",
         views.leave_request_add, name="leave_request_add"),
    path("<int:pk>/",
         views.leave_request_detail, name="leave_request_detail"),
    path("<int:pk>/approve/",
         views.leave_approve, name="leave_approve"),
    path("<int:pk>/reject/",
         views.leave_reject, name="leave_reject"),
    path("<int:pk>/cancel/",
         views.leave_cancel, name="leave_cancel"),

    # الأرصدة
    path("balances/",
         views.leave_balances, name="leave_balances"),
    path("balances/set/",
         views.set_leave_balance, name="set_leave_balance"),
]
