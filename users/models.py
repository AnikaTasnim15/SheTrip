from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    age = models.IntegerField(default=0, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    languages = models.CharField(max_length=200, blank=True)
    travel_style = models.CharField(max_length=50, blank=True)
    accommodation = models.CharField(max_length=200, blank=True)
    interests = models.CharField(max_length=500, blank=True)
    dream_destinations = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    verification_status = models.CharField(
    max_length=20, 
    choices=[
        ('not_submitted', 'Not Submitted'),
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ],
    default='not_submitted'
    )
    nid_front = models.ImageField(upload_to='verification/nid_front/', blank=True, null=True)
    nid_back = models.ImageField(upload_to='verification/nid_back/', blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def is_verified(self):
        """Check if user's account is verified"""
        return self.verification_status == 'verified'
    
    @property
    def is_profile_complete(self):
        """Check if user has completed their profile"""
        required_fields = [
            self.age and self.age > 0 and
            self.city and 
            self.country and 
            self.travel_style
        ]
        return all(required_fields) and self.age > 0
    
    def get_verification_badge(self):
        """Return verification badge HTML for templates"""
        if self.verification_status == 'verified':
            return '✅ Verified'
        elif self.verification_status == 'pending':
            return '⏳ Pending'
        elif self.verification_status == 'rejected':
            return '❌ Rejected'
        else:
            return '📋 Not Verified'
    
    def can_access_trips(self):
        """Check if user can access trip features"""
        return self.verification_status == 'verified'


class UserConnection(models.Model):
    """Model for user connections/friendships"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('connected', 'Connected'),
        ('blocked', 'Blocked'),
    ]

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_received')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

    def accept(self):
        """Accept a connection request"""
        self.status = 'connected'
        self.save()

    def reject(self):
        """Reject a connection request"""
        self.delete()

    def block(self):
        """Block a user"""
        self.status = 'blocked'
        self.save()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('connection_request', 'Connection Request'),
        ('connection_accepted', 'Connection Accepted'),
        ('connection_rejected', 'Connection Rejected'),
        ('trip_invitation', 'Trip Invitation'),
        ('message', 'New Message'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)  # URL to redirect when clicked
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.username}"
