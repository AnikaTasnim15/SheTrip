from django.urls import path
from . import views

urlpatterns = [
    # Payment processing
    path('checkout/<int:trip_id>/', views.checkout_view, name='payments_checkout'),
    path('refund/<int:trip_id>/', views.refund_view, name='payments_refund'),
    
    # Trip payment routes
    path('trip/<int:trip_id>/', views.trip_payment_view, name='trip_payment'),
    path('trip/<int:trip_id>/cancel/', views.trip_cancel_payment_view, name='trip_cancel_payment'),
    path('history/', views.payments_history_view, name='payments_history'),
    
    # SSLCommerz callback URLs
    path('success/', views.payment_success_view, name='payment_success'),
    path('fail/', views.payment_fail_view, name='payment_fail'),
    path('cancel/', views.payment_cancel_view, name='payment_cancel'),
    path('ipn/', views.payment_ipn_view, name='payment_ipn'),
]