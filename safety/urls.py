from django.urls import path
from . import views

app_name = 'safety'

urlpatterns = [
    path('', views.safety_list, name='safety_list'),
    path('create/', views.safety_create, name='safety_create'),
    path('<int:pk>/', views.safety_detail, name='safety_detail'),
    # Guidelines
    path('guidelines/', views.guidelines_index, name='guidelines_index'),
    path('guidelines/verify-before-meeting/', views.verify_before_meeting, name='verify_before_meeting'),
    path('guidelines/share-location/', views.share_location, name='share_location'),
    path('guidelines/emergency-support/', views.emergency_support, name='emergency_support'),
]
