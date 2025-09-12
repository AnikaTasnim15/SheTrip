from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),  # Add this line
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]