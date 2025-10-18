from django.contrib import admin
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    TravelPlan, Driver, OrganizedTrip, TripParticipant,
    TravelMatch, Payment, Revenue, TravelPlanInterest
)

@admin.register(TravelPlan)
class TravelPlanAdmin(admin.ModelAdmin):
    list_display = ['destination', 'user', 'start_date', 'end_date', 'status', 'is_active', 'join_deadline', 'admin_warning', 'get_combined_transport']
    list_filter = ['purpose', 'budget_range', 'is_active', 'start_date', 'status']
    search_fields = ['destination', 'user__username', 'description']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at', 'payment_deadline', 'join_deadline', 'start_date', 'end_date', 'destination', 'user', 'purpose', 'budget_range', 'max_participants', 'description']

    
    fieldsets = (
        ('Plan Information', {
            'fields': ('destination', 'user', 'start_date', 'end_date', 'purpose', 'budget_range', 'max_participants', 'description', 'is_active')
        }),
        ('Status & Timeline', {
            'fields': ('status', 'join_deadline', 'payment_deadline', 'admin_warning'),
            'description': 'Admin controls and warnings'
        }),
        ('Logistics (Assign when status=finalized)', {
            'fields': ('transportation_details', 'accommodation_details', 'meal_arrangements', 'itinerary', 'assigned_driver'),
            'classes': ('collapse',)
        }),
        ('Cost Details - Separate Assignment (shown combined to users)', {
    'fields': (
        'accommodation_cost', 
        'food_cost', 
        'transportation_cost', 
        'driver_payment', 
        'combined_transportation_cost',
        'other_costs',
        'base_cost', 
        'platform_commission', 
        'final_cost_per_person', 
        'profit_margin'
     ),
    'description': 'Admin assigns costs separately here. Users see transportation_cost + driver_payment combined as "Transportation Fee"',
    'classes': ('collapse',)
    }),
    )
    
    actions = ['mark_as_finalized', 'reject_plan']

    def reject_plan(self, request, queryset):
        """Admin can reject any plan at any time"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} plans have been rejected.')
    reject_plan.short_description = "Reject selected plans"


    def get_combined_transport(self, obj):
        if obj.transportation_cost and obj.driver_payment:
            combined = obj.transportation_cost + obj.driver_payment
            return f"৳{combined} (Transport: ৳{obj.transportation_cost} + Driver: ৳{obj.driver_payment})"
        return "Not assigned"
    get_combined_transport.short_description = "Combined Transportation"
    
    def mark_as_finalized(self, request, queryset):
        """Quick action to mark plans as finalized"""
        from django.utils import timezone
        from datetime import timedelta
    
        updated_count = 0
        for plan in queryset.filter(status='closed'):
            plan.status = 'finalized'
            plan.payment_deadline = timezone.now() + timedelta(minutes=5)  
            plan.save()
            updated_count += 1
        self.message_user(request, f'{updated_count} plans marked as finalized with 5-minute payment deadline.')
    mark_as_finalized.short_description = "Mark selected closed plans as finalized"

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'license_number', 'rating', 'is_verified', 'is_available']
    list_filter = ['is_verified', 'is_available']
    search_fields = ['name', 'phone_number', 'license_number']

@admin.register(OrganizedTrip)
class OrganizedTripAdmin(admin.ModelAdmin):
    list_display = ['trip_name', 'destination', 'trip_status', 'total_participants', 'departure_time', 'driver', 'driver_payment']
    list_filter = ['trip_status', 'departure_time']
    search_fields = ['trip_name', 'destination']
    date_hierarchy = 'departure_time'
    readonly_fields = ['created_at']
    fieldsets = (
        ('Trip Information', {
            'fields': ('trip_name', 'destination', 'travel_plan', 'departure_time', 'return_time', 'total_participants')
        }),
        ('Cost Details', {
            'fields': ('base_cost', 'platform_commission', 'final_cost_per_person', 'profit_margin')
        }),
        ('Logistics', {
            'fields': ('driver', 'transportation_details', 'accommodation_details', 'meal_arrangements', 'itinerary')
        }),
        ('Status', {
            'fields': ('trip_status',)
        }),
    )

@admin.register(TripParticipant)
class TripParticipantAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'trip', 
        'payment_status', 
        'attendance_status', 
        'emergency_contact',  
        'face_verification_done', 
        'join_date'
    ]
    list_filter = ['payment_status', 'attendance_status', 'face_verification_done']
    search_fields = ['user__username', 'trip__trip_name', 'emergency_contact']  # ✅ ADD emergency_contact
    date_hierarchy = 'join_date'
    
    #  ADD fieldsets to organize admin view
    fieldsets = (
        ('Participant Info', {
            'fields': ('user', 'trip', 'join_date')
        }),
        ('Payment Details', {
            'fields': ('payment_status', 'amount_paid', 'commission_charged')
        }),
        ('Trip Information', {
            'fields': ('emergency_contact', 'special_requirements', 'attendance_status', 'face_verification_done')
        }),
    )
    readonly_fields = ['join_date']

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

@admin.register(TravelPlanInterest)
class TravelPlanInterestAdmin(admin.ModelAdmin):
    list_display = ['plan', 'user', 'agreed', 'joined_at', 'agreed_at']
    list_filter = ['agreed', 'joined_at']
    search_fields = ['plan__destination', 'user__username']


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ['trip', 'total_trip_revenue', 'platform_commission', 'net_profit', 'date_recorded']
    search_fields = ['trip__trip_name']
    date_hierarchy = 'date_recorded'
    readonly_fields = ['date_recorded']

@receiver(post_save, sender=TravelPlan)
def recalculate_plan_costs(sender, instance, **kwargs):
    """Recalculate combined costs when admin updates plan"""
    if instance.accommodation_cost and instance.food_cost and instance.transportation_cost and instance.driver_payment:
        combined_transport = instance.transportation_cost + instance.driver_payment
        final_cost = (
            instance.accommodation_cost + 
            instance.food_cost + 
            combined_transport +
            (instance.other_costs or 0)
        )
        
        # Only update if values changed
        if instance.combined_transportation_cost != combined_transport or instance.final_cost_per_person != final_cost:
            TravelPlan.objects.filter(pk=instance.pk).update(
                combined_transportation_cost=combined_transport,
                final_cost_per_person=final_cost
            )