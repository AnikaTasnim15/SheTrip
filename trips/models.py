from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class TravelPlan(models.Model):
    """User-created travel plans that can be matched with others
    
    This model supports a 5-minute join window and lifecycle statuses
    to facilitate the Find Buddies → Organized Trip funnel.
    
    Minimum 2 participants, maximum 5 participants. Budget up to 50,000 BDT.
    Duration 2-14 days.
    """

    
    PURPOSE_CHOICES = [
        ('leisure', 'Leisure/Vacation'),
        ('adventure', 'Adventure'),
        ('cultural', 'Cultural Experience'),
        ('religious', 'Religious/Pilgrimage'),
        ('other', 'Other'),
    ]

    BUDGET_CHOICES = [
        ('budget', 'Budget (< 10,000 BDT)'),
        ('mid-range', 'Mid-Range (10,000 - 30,000 BDT)'),
        ('luxury', 'Luxury (30,000 - 50,000 BDT)'),
    ]

    plan_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_plans')
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES)
    budget_range = models.CharField(max_length=20, choices=BUDGET_CHOICES)
    description = models.TextField(blank=True)
    max_participants = models.IntegerField(
        default=5,
        validators=[MinValueValidator(2), MaxValueValidator(5)]
    )
    
    is_active = models.BooleanField(default=True)
    
    # Lifecycle fields
    STATUS_CHOICES = [
        ('open', 'Open'),            # Accepting interests (5 minutes or admin closes)
        ('closed', 'Closed'),        # Auto-closed after 5 min or admin closed
        ('finalized', 'Finalized'),  # Admin finalized details
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),    # Final admin approval after min 2 payments
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    join_deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    admin_warning = models.TextField(blank=True, null=True, help_text="Admin warning about this plan if inconsistencies detected")
    payment_deadline = models.DateTimeField(null=True, blank=True)
    
    transportation_details = models.TextField(blank=True, null=True)
    accommodation_details = models.TextField(blank=True, null=True)
    meal_arrangements = models.TextField(blank=True, null=True)
    itinerary = models.TextField(blank=True, null=True)
    base_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    final_cost_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    assigned_driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_trips')
    driver_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True, help_text="Payment amount for the assigned driver for this specific trip")
    # Separate cost tracking (admin assigns these)
    accommodation_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True, help_text="Accommodation fee per person")
    food_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True, help_text="Food/meals cost per person")
    transportation_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True, help_text="Transportation cost per person (includes driver payment)")
    other_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True, help_text="Other miscellaneous costs per person")

    # Combined cost shown to users
    combined_transportation_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True, help_text="Combined transportation (transportation_cost + driver_payment) shown to users")
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.destination} - {self.user.username} ({self.start_date})"
     


    def clean(self):
     """Validate duration is between 2-14 days"""
     from django.core.exceptions import ValidationError
     if self.start_date and self.end_date:
        duration = (self.end_date - self.start_date).days + 1
        if duration < 2 or duration > 14:
            raise ValidationError("Trip duration must be between 2 and 14 days")

    def duration_days(self):
        return (self.end_date - self.start_date).days + 1
    
    def save(self, *args, **kwargs):
        """Override save to set join_deadline and auto-close expired plans"""
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        
        # ADD at start of save() method:
        try:
            self.full_clean()
        except ValidationError:
            pass
        

        # For new instances, set join_deadline before saving (5 minutes)
        is_new = self.pk is None
        if is_new and self.join_deadline is None:
            self.join_deadline = timezone.now() + timedelta(minutes=5)
    
        
        if self.accommodation_cost and self.food_cost and self.transportation_cost and self.driver_payment:
            self.combined_transportation_cost = self.transportation_cost + self.driver_payment
            self.final_cost_per_person = (
                self.accommodation_cost + 
                self.food_cost + 
                self.combined_transportation_cost +  
                (self.other_costs or 0)
            )
        super().save(*args, **kwargs)

    @property
    def interest_count(self) -> int:
        return getattr(self, 'interests', None).count() if hasattr(self, 'interests') else 0
    
    @property
    def interested_users_count(self):
        return self.interests.count()
    
    @property
    def is_join_window_open(self) -> bool:
        if self.status != 'open':
            return False
        if not self.join_deadline:
            return True
        return timezone.now() <= self.join_deadline


class Driver(models.Model):
    """Verified drivers for organized trips"""
    driver_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    license_number = models.CharField(max_length=50, unique=True)
    vehicle_details = models.TextField()
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    payment_rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    emergency_contact = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} - {self.vehicle_details}"


class OrganizedTrip(models.Model):
    """Fully organized trips by SheTrip admin"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('open', 'Open for Registration'),
        ('confirmed', 'Confirmed'),  # Minimum 2 paid participants
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    trip_id = models.AutoField(primary_key=True)
    travel_plan = models.OneToOneField(
        TravelPlan,
        on_delete=models.CASCADE,
        related_name='organized_trip',
        null=True,
        blank=True
    )
    trip_name = models.CharField(max_length=200)
    total_participants = models.IntegerField(default=0)
    base_cost = models.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    final_cost_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    transportation_details = models.TextField()
    accommodation_details = models.TextField()
    meal_arrangements = models.TextField()
    trip_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        related_name='trips'
    )
    profit_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    driver_payment = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
       help_text="Payment amount for the assigned driver"
  )
    created_at = models.DateTimeField(auto_now_add=True)
    departure_time = models.DateTimeField()
    return_time = models.DateTimeField()
    destination = models.CharField(max_length=200)
    itinerary = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.trip_name} - {self.trip_status}"

    def available_slots(self):
        if self.travel_plan:
            return self.travel_plan.max_participants - self.total_participants
        return 0
    
    @property
    def is_finalized(self) -> bool:
        return self.trip_status in ['confirmed', 'ongoing', 'completed']
     
    def save(self, *args, **kwargs):
        if self.travel_plan:
        # Inherit all details from TravelPlan
            self.transportation_details = self.travel_plan.transportation_details or ''
            self.accommodation_details = self.travel_plan.accommodation_details or ''
            self.meal_arrangements = self.travel_plan.meal_arrangements or ''
            self.itinerary = self.travel_plan.itinerary or ''
            self.driver = self.travel_plan.assigned_driver
            self.driver_payment = self.travel_plan.driver_payment or 0
            self.final_cost_per_person = self.travel_plan.final_cost_per_person or 0
            self.platform_commission = self.travel_plan.platform_commission or 0
        
        super().save(*args, **kwargs)

class TravelPlanInterest(models.Model):
    """Users expressing interest (pre-payment) in a TravelPlan during the 5-minute window"""

    id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(TravelPlan, on_delete=models.CASCADE, related_name='interests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_plan_interests')
    joined_at = models.DateTimeField(auto_now_add=True)
    agreed = models.BooleanField(default=False)
    agreed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['plan', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"Interest: {self.user.username} -> {self.plan.destination}"


class TripParticipant(models.Model):
    """Junction table for users participating in organized trips"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]

    ATTENDANCE_STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    participant_id = models.AutoField(primary_key=True)
    trip = models.ForeignKey(
        OrganizedTrip,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trip_participations'
    )
    join_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_charged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default='registered'
    )
    face_verification_done = models.BooleanField(default=False)
    
    # ✅ ADD THESE TWO FIELDS:
    emergency_contact = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Emergency contact number for this trip"
    )
    special_requirements = models.TextField(
        blank=True, 
        null=True,
        help_text="Dietary restrictions, medical needs, or special requests"
    )

    class Meta:
        unique_together = ['trip', 'user']
        ordering = ['join_date']

    def __str__(self):
        return f"{self.user.username} - {self.trip.trip_name}"


class TravelMatch(models.Model):
    """Matches between compatible travel plans"""
    MATCH_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    match_id = models.AutoField(primary_key=True)
    travel_plan_1 = models.ForeignKey(
        TravelPlan,
        on_delete=models.CASCADE,
        related_name='matches_as_plan_1'
    )
    travel_plan_2 = models.ForeignKey(
        TravelPlan,
        on_delete=models.CASCADE,
        related_name='matches_as_plan_2'
    )
    compatibility_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    match_status = models.CharField(
        max_length=20,
        choices=MATCH_STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['travel_plan_1', 'travel_plan_2']
        ordering = ['-compatibility_score', '-created_at']

    def __str__(self):
        return f"Match: {self.travel_plan_1.destination} - Score: {self.compatibility_score}%"


class Payment(models.Model):
    """Payment records for trips - DUMMY PAYMENTS FOR TESTING"""
    PAYMENT_METHOD_CHOICES = [
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    payment_id = models.AutoField(primary_key=True)
    trip = models.ForeignKey(
        OrganizedTrip,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    refund_status = models.BooleanField(default=False)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.user.username}"


class Revenue(models.Model):
    """Revenue tracking for each trip"""
    revenue_id = models.AutoField(primary_key=True)
    trip = models.OneToOneField(
        OrganizedTrip,
        on_delete=models.CASCADE,
        related_name='revenue'
    )
    total_trip_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=12, decimal_places=2)
    driver_payment = models.DecimalField(max_digits=10, decimal_places=2)
    operational_costs = models.DecimalField(max_digits=10, decimal_places=2)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2)
    date_recorded = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Revenues"

    def __str__(self):
        return f"Revenue for {self.trip.trip_name}: {self.net_profit} BDT"