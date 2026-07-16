from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('js-solutions/', views.js_solutions_home, name='js_solutions'),
    path('', views.smart_home, name='home'),
    path('about/', views.landing_about, name='about'),
    path('contact/', views.landing_contact, name='contact'),
    path('pricing/', views.landing_pricing, name='pricing'),
    path('free-trial/', views.free_trial_register, name='free_trial'),
    path('free-trial/success/', views.free_trial_success, name='free_trial_success'),
]