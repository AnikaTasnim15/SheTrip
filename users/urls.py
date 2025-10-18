from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.urls import reverse_lazy

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('verification/', views.verification_view, name='verification'),

    path('settings/', views.settings_view, name='settings'),
    path('help/', views.help_support_view, name='help_support'),
    path('support/submit/', views.submit_support_ticket, name='submit_support_ticket'),
    path('account/delete/', views.delete_account_confirmation_view, name='delete_account_confirm'),
    path('account/delete/confirm/', views.delete_account_view, name='delete_account'),
    # Password reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ),
         name='password_reset_confirm'),

    path('community/', views.community_view, name='community'),
    path('community/send-request/<int:user_id>/', views.send_connection_request, name='send_connection_request'),
    path('community/accept/<int:connection_id>/', views.accept_connection, name='accept_connection'),
    path('community/reject/<int:connection_id>/', views.reject_connection, name='reject_connection'),
    path('community/my-connections/', views.my_connections, name='my_connections'),
    path('connections/', views.connections_list, name='connections_list'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
]