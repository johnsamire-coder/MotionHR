from django.urls import path
from . import views

app_name = "requests_app"

urlpatterns = [
    path("",               views.requests_list,   name="list"),
    path("add/",           views.request_add,     name="add"),
    path("<int:pk>/",      views.request_detail,  name="detail"),
    path("<int:pk>/approve/", views.request_approve, name="approve"),
    path("<int:pk>/reject/",  views.request_reject,  name="reject"),
    path("<int:pk>/cancel/",  views.request_cancel,  name="cancel"),
]
