from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from allauth.account.signals import user_logged_in
from django.contrib.auth.models import User
from .models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SocialAccount)
def create_incomplete_profile_for_social_user(sender, instance, created, **kwargs):
    """Create INCOMPLETE UserProfile for social login users"""
    if not created:
        return

    user = instance.user
    if hasattr(user, 'userprofile'):
        return

    try:
        # Create MINIMAL profile - FORCES profile completion and verification
        profile = UserProfile.objects.create(
            user=user,
            # Invalid/empty required fields
            age=0,  
            city='',
            country='',
            travel_style='',
            verification_status='not_submitted'  # Force verification
        )
        logger.info(f"Created incomplete profile for social user {user.username}")
        
    except Exception as exc:
        logger.error(f"Failed to create UserProfile for social user {user.pk}: {exc}")


@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    """
    Backup signal to ensure ALL users have a profile.
    Creates incomplete profile if none exists.
    """
    if created and not hasattr(instance, 'userprofile'):
        try:
            UserProfile.objects.create(
                user=instance,
                age=0,  # Invalid - forces update
                city='',
                country='',
                travel_style='',
                verification_status='not_submitted'
            )
            logger.info(f"Created profile for user {instance.username} via post_save signal")
        except Exception as exc:
            logger.exception(f"Failed to create profile in post_save: {exc}")


@receiver(user_logged_in)
def set_jwt_on_social_login(sender, request, user, **kwargs):
    """Set JWT tokens when user logs in via social auth"""
    if request:
        refresh = RefreshToken.for_user(user)
        request.session['jwt_access'] = str(refresh.access_token)
        request.session['jwt_refresh'] = str(refresh)