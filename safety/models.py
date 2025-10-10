from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# Import OrganizedTrip if you need it for SOS/Safety reports
# from trips.models import OrganizedTrip


class SafetyReport(models.Model):
    """Safety reports filed by users"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    REPORT_TYPE_CHOICES = [
        ('harassment', 'Harassment'),
        ('unsafe_driver', 'Unsafe Driver'),
        ('unsafe_accommodation', 'Unsafe Accommodation'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('accident', 'Accident'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='filed_reports'
    )
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES, default='other')
    description = models.TextField()
    severity_level = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    location = models.CharField(max_length=300, blank=True)

    # Optional: Link to trip if report is trip-related
    # trip = models.ForeignKey(OrganizedTrip, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if self.resolved and not self.resolved_at:
            self.resolved_at = timezone.now()
            self.status = 'resolved'
        super().save(*args, **kwargs)


class SafetyGuideline(models.Model):
    """Safety guidelines and tips for travelers"""
    CATEGORY_CHOICES = [
        ('general', 'General Safety'),
        ('travel', 'Travel Safety'),
        ('accommodation', 'Accommodation Safety'),
        ('transportation', 'Transportation Safety'),
        ('communication', 'Communication Safety'),
        ('emergency', 'Emergency Procedures'),
        ('health', 'Health & Wellness'),
        ('cultural', 'Cultural Sensitivity'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    content = models.TextField()
    short_description = models.TextField(max_length=300, blank=True)
    icon = models.CharField(max_length=50, default='fa-shield-alt')
    priority = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Higher priority guidelines appear first"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'title']

    def __str__(self):
        return self.title


class EmergencyContact(models.Model):
    """User's emergency contacts for safety"""
    RELATIONSHIP_CHOICES = [
        ('parent', 'Parent'),
        ('spouse', 'Spouse'),
        ('sibling', 'Sibling'),
        ('friend', 'Friend'),
        ('relative', 'Relative'),
        ('partner', 'Partner'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emergency_contacts'
    )
    contact_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES)
    phone_number = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', 'contact_name']
        verbose_name_plural = "Emergency Contacts"

    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.contact_name} - {self.user.username}{primary}"

    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary contacts
        if self.is_primary:
            EmergencyContact.objects.filter(
                user=self.user,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class SOSAlert(models.Model):
    """Emergency SOS alerts raised by users"""
    ALERT_TYPE_CHOICES = [
        ('emergency', 'General Emergency'),
        ('medical', 'Medical Emergency'),
        ('safety_threat', 'Safety Threat'),
        ('accident', 'Accident'),
        ('lost', 'Lost/Separated'),
        ('harassment', 'Harassment'),
        ('vehicle_issue', 'Vehicle Issue'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('responding', 'Help On The Way'),
        ('resolved', 'Resolved'),
        ('false_alarm', 'False Alarm'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sos_alerts'
    )
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES, default='emergency')

    # Location data
    location_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    location_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    location_address = models.CharField(max_length=500, blank=True)

    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Admin handling
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_sos_alerts'
    )
    admin_notes = models.TextField(blank=True)

    # Emergency contacts notified
    contacts_notified = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "SOS Alert"
        verbose_name_plural = "SOS Alerts"

    def __str__(self):
        return f"SOS Alert from {self.user.username} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if self.status in ['resolved', 'false_alarm'] and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)