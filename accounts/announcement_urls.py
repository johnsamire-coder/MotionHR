from django.urls import path
from . import announcement_views

app_name = 'announcements'

urlpatterns = [
    path('', announcement_views.announcements_list, name='list'),
    path('create/', announcement_views.announcement_create, name='create'),
    path('<int:pk>/', announcement_views.announcement_detail, name='detail'),
    path('<int:pk>/delete/', announcement_views.announcement_delete, name='delete'),
]
