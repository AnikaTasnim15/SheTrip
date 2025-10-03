from django.contrib import admin
from .models import (
    TravelPlan, Driver, OrganizedTrip, TripParticipant,
    TravelMatch, Payment, Revenue
)

@admin.register(TravelPlan)
class TravelPlanAdmin(admin.ModelAdmin):
    list_display = ['destination', 'user', 'start_date', 'end_date', 'purpose', 'budget_range', 'is_active']
    list_filter = ['purpose', 'budget_range', 'is_active', 'start_date']
    search_fields = ['destination', 'user__username', 'description']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'license_number', 'rating', 'is_verified', 'is_available']
    list_filter = ['is_verified', 'is_available']
    search_fields = ['name', 'phone_number', 'license_number']

@admin.register(OrganizedTrip)
class OrganizedTripAdmin(admin.ModelAdmin):
    list_display = ['trip_name', 'destination', 'trip_status', 'total_participants', 'departure_time', 'driver']
    list_filter = ['trip_status', 'departure_time']
    search_fields = ['trip_name', 'destination']
    date_hierarchy = 'departure_time'
    readonly_fields = ['created_at']

@admin.register(TripParticipant)
class TripParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'trip', 'payment_status', 'attendance_status', 'face_verification_done', 'join_date']
    list_filter = ['payment_status', 'attendance_status', 'face_verification_done']
    search_fields = ['user__username', 'trip__trip_name']
    date_hierarchy = 'join_date'

@admin.register(TravelMatch)
class TravelMatchAdmin(admin.ModelAdmin):
    list_display = ['travel_plan_1', 'travel_plan_2', 'compatibility_score', 'match_status', 'created_at']
    list_filter = ['match_status', 'created_at']
    search_fields = ['travel_plan_1__destination', 'travel_plan_2__destination']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'trip', 'total_amount', 'payment_method', 'payment_status', 'payment_date']
    list_filter = ['payment_method', 'payment_status', 'refund_status']
    search_fields = ['transaction_id', 'user__username', 'trip__trip_name']
    date_hierarchy = 'payment_date'

@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ['trip', 'total_trip_revenue', 'platform_commission', 'net_profit', 'date_recorded']
    search_fields = ['trip__trip_name']
    date_hierarchy = 'date_recorded'
    readonly_fields = ['date_recorded']
