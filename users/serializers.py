from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id']
    
    def get_profile(self, obj):
        try:
            profile = obj.userprofile
            return {
                'city': profile.city,
                'country': profile.country,
                'age': profile.age,
                'travel_style': profile.travel_style,
                'verification_status': profile.verification_status,
                'profile_picture': profile.profile_picture.url if profile.profile_picture else None,
            }
        except UserProfile.DoesNotExist:
            return None