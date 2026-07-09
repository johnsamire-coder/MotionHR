from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employee_list, name='list'),
    path('add/', views.employee_add, name='add'),
    path('<int:pk>/', views.employee_detail, name='detail'),
    path('<int:pk>/edit/', views.employee_edit, name='edit'),
    path('<int:pk>/delete/', views.employee_delete, name='delete'),
    
    # الطباعة
    path('print/', views.employee_print, name='print_all'),
    path('<int:pk>/print/', views.employee_print_detail, name='print_detail'),
]