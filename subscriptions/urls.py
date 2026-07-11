from django.urls import path
from . import views
from .views import contact_sales_view

app_name = 'subscriptions'

urlpatterns = [
    path('upgrade/module/<str:feature_code>/', views.feature_upsell_page, name='upsell'),


    # ── Admin Dashboard ──────────────────────────────────
    path('', views.admin_dashboard, name='admin_dashboard'),

    # ── Plans ────────────────────────────────────────────
    path('plans/', views.plans_list, name='plans_list'),

    # ── Subscriptions (Admin) ────────────────────────────
    path('subscriptions/',
         views.subscriptions_list, name='subscriptions_list'),
    path('subscriptions/create/',
         views.create_subscription, name='create'),
    path('subscriptions/<int:pk>/',
         views.subscription_detail, name='detail'),
    path('subscriptions/<int:pk>/upgrade/',
         views.upgrade_subscription, name='upgrade'),
    path('subscriptions/<int:pk>/extend/',
         views.extend_subscription, name='extend'),
    path('subscriptions/<int:pk>/cancel/',
         views.cancel_subscription, name='cancel'),
    path('subscriptions/<int:pk>/activate/',
         views.activate_subscription, name='activate'),

    # ── Client Side ──────────────────────────────────────
    path('my-subscription/',
         views.my_subscription, name='my_subscription'),
    path('my-plan/',
         views.my_plan_view, name='my_plan'),
    path('upgrade/',
         views.upgrade_plan, name='upgrade_plan'),
    path('feature-locked/',
         views.feature_locked, name='feature_locked'),
    path('contact-sales/',
         contact_sales_view, name='contact_sales'),
]
