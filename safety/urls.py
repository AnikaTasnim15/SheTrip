from django.urls import path
from . import views

app_name = 'safety'

urlpatterns = [
    # Safety Center
    path('', views.safety_center, name='safety_center'),

    # Emergency Contacts
    path('emergency-contacts/', views.emergency_contacts, name='emergency_contacts'),
    path('emergency-contacts/add/', views.add_emergency_contact, name='add_emergency_contact'),
    path('emergency-contacts/<int:contact_id>/edit/', views.edit_emergency_contact, name='edit_emergency_contact'),
    path('emergency-contacts/<int:contact_id>/delete/', views.delete_emergency_contact,
         name='delete_emergency_contact'),

    # SOS Alerts
    path('sos/', views.sos_alerts, name='sos_alerts'),
    path('sos/create/', views.create_sos_alert, name='create_sos_alert'),
    path('sos/<int:alert_id>/', views.sos_alert_detail, name='sos_alert_detail'),
    path('sos/quick/', views.quick_sos, name='quick_sos'),

    # Safety Guidelines
    path('guidelines/', views.guidelines_index, name='guidelines_index'),
    path('guidelines/verify-before-meeting/', views.verify_before_meeting, name='verify_before_meeting'),
    path('guidelines/share-location/', views.share_location, name='share_location'),
    path('guidelines/emergency-support/', views.emergency_support, name='emergency_support'),
    path('guidelines/<slug:slug>/', views.guideline_detail, name='guideline_detail'),

    # Safety Reports
    path('reports/', views.safety_list, name='safety_list'),
    path('reports/create/', views.safety_create, name='safety_create'),
    path('reports/my-reports/', views.my_reports, name='my_reports'),
    path('reports/<int:pk>/', views.safety_detail, name='safety_detail'),
]
