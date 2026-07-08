from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # سجلات الحضور
    path('', views.attendance_list, name='list'),
    
    # Check-in/out
    path('check-in/', views.check_in_page, name='check_in'),
    path('api/check-in/', views.api_check_in, name='api_check_in'),
    path('api/check-out/', views.api_check_out, name='api_check_out'),
    
    # زيارات المواقع
    path('visits/', views.visits_list, name='visits'),
    path('visits/add/', views.visit_add, name='visit_add'),
    
    # الخريطة
    path('map/', views.live_map, name='live_map'),
    path('api/live-locations/', views.api_live_locations, name='api_live_locations'),
]