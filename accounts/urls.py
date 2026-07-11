from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login-settings/', views.login_settings_view, name='login_settings'),
    path('profile/',        views.profile_view,         name='profile'),
    path('profile/update/', views.profile_update,       name='profile_update'),
    path('notifications/',  views.notifications_view,   name='notifications'),

    path('notifications/send/', views.send_employee_notification_view, name='send_employee_notification'),

    path('push-subscribe/', views.push_subscribe, name='push_subscribe'),
    path('push-unsubscribe/', views.push_unsubscribe, name='push_unsubscribe'),
]
