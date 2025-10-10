from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    age = models.IntegerField()
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    occupation = models.CharField(max_length=100, blank=True)
    languages = models.CharField(max_length=200, blank=True)
    travel_style = models.CharField(max_length=50)
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