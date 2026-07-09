from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Plans
    path('plans/', views.plans_list, name='plans_list'),
    
    # Subscriptions
    path('subscriptions/', views.subscriptions_list, name='subscriptions_list'),
    path('subscriptions/<int:pk>/', views.subscription_detail, name='detail'),
    path('subscriptions/create/', views.create_subscription, name='create'),
    path('subscriptions/<int:pk>/upgrade/', views.upgrade_subscription, name='upgrade'),
    path('subscriptions/<int:pk>/extend/', views.extend_subscription, name='extend'),
    path('subscriptions/<int:pk>/cancel/', views.cancel_subscription, name='cancel'),
    path('subscriptions/<int:pk>/activate/', views.activate_subscription, name='activate'),
]
