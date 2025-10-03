from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class TravelPlan(models.Model):
    """User-created travel plans that can be matched with others"""
    PURPOSE_CHOICES = [
        ('leisure', 'Leisure/Vacation'),
        ('business', 'Business'),
        ('adventure', 'Adventure'),
        ('cultural', 'Cultural Experience'),
        ('religious', 'Religious/Pilgrimage'),
        ('family', 'Family Visit'),
        ('other', 'Other'),
    ]

    BUDGET_CHOICES = [
        ('budget', 'Budget (< 5,000 BDT)'),
        ('mid-range', 'Mid-Range (5,000 - 15,000 BDT)'),
        ('luxury', 'Luxury (> 15,000 BDT)'),
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
        default=6,
        validators=[MinValueValidator(2), MaxValueValidator(50)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.destination} - {self.user.username} ({self.start_date})"

    def duration_days(self):
        return (self.end_date - self.start_date).days + 1


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
        ('confirmed', 'Confirmed'),
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
    """Payment records for trips"""
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
