from django.urls import path
from . import views

urlpatterns = [
    # My Trips
    path('my-trips/', views.my_trips_view, name='my_trips'),
    
    # Travel Plan Management
    path('create-plan/', views.create_travel_plan_view, name='create_travel_plan'),
    path('plan/<int:plan_id>/', views.travel_plan_detail_view, name='travel_plan_detail'),
    path('plan/<int:plan_id>/edit/', views.edit_travel_plan_view, name='edit_travel_plan'),
    path('plan/<int:plan_id>/delete/', views.delete_travel_plan_view, name='delete_travel_plan'),
    
    # Find Travel Buddies
    path('find-buddies/', views.find_travel_buddies_view, name='find_buddies'),
    path('matches/', views.trip_matches_view, name='trip_matches'),
    
    # Organized Trips
    path('organized/', views.organized_trips_view, name='organized_trips'),
    path('organized/<int:trip_id>/', views.organized_trip_detail_view, name='organized_trip_detail'),
    path('organized/<int:trip_id>/join/', views.join_organized_trip_view, name='join_organized_trip'),
    path('organized/<int:trip_id>/leave/', views.leave_organized_trip_view, name='leave_organized_trip'),
]