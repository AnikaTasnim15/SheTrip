from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.models import User


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to redirect social login users to profile completion
    and verification pages.
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Link social account to existing user if email matches
        """
        if sociallogin.is_existing:
            return
        
        email = sociallogin.account.extra_data.get('email', None)
        if not email:
            return
        
        try:
           user = User.objects.get(email=email)
            # Connect social account to this user
           sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass  # No existing user, proceed normally

    def get_connect_redirect_url(self, request, socialaccount):
        """
        Redirect after connecting a social account
        """
        return '/dashboard/'
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user and ensure profile will be created by signal
        """
        user = super().save_user(request, sociallogin, form)
        return user
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user with data from social provider
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Get data from provider
        extra_data = sociallogin.account.extra_data
        
        # Set names if not already set
        if not user.first_name:
            user.first_name = extra_data.get('given_name', '') or extra_data.get('first_name', '')
        
        if not user.last_name:
            user.last_name = extra_data.get('family_name', '') or extra_data.get('last_name', '')
        
        # Set email if not already set
        if not user.email:
            user.email = extra_data.get('email', '')
        
        return user
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Allow automatic signup for social accounts.
        Profile will be incomplete and force verification.
        """
        return True