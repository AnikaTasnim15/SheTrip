from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"{self.user.username}'s Profile"