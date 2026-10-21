from django.urls import path

from . import api

app_name = 'biometric'

urlpatterns = [
    path('api/devices/', api.devices, name='devices'),
    path('api/devices/<int:device_id>/', api.device_detail, name='device_detail'),
    path('api/user-map/', api.user_map, name='user_map'),
    path('api/upload/', api.upload, name='upload'),
    path('api/report/', api.report, name='report'),
]
