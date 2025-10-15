from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from users.models import UserProfile

class VerificationMiddleware:
    """
    Middleware to check if user is verified before accessing trip-related pages
    """
    
    # URLs that require verification
    PROTECTED_URLS = [
        'find_buddies',
        'create_travel_plan',
        'edit_travel_plan',
        'travel_plan_detail',
        'delete_travel_plan',
        'my_trips',
        'organized_trips',
        'organized_trip_detail',
        'join_organized_trip',
        'leave_organized_trip',
    ]
    
    # URLs that are always accessible (even without verification)
    ALLOWED_URLS = [
        'home',
        'login',
        'logout',
        'register',
        'dashboard',
        'verification',
        'edit_profile',
        'password_reset',
        'password_reset_done',
        'password_reset_confirm',
        'password_reset_complete',
        'admin:index',  # Allow admin access
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Allow home page access without any checks
        if request.path == '/':
            return self.get_response(request)
        
        # Allow access if user is not authenticated
        if not request.user.is_authenticated:
            return self.get_response(request)
            
        if request.user.is_superuser or request.user.is_staff:
            return self.get_response(request)

        current_url = request.resolver_match.url_name if request.resolver_match else None
        
        # Only check verification for protected URLs
        if current_url in self.PROTECTED_URLS:
            try:
                profile = request.user.userprofile
                is_social = hasattr(request.user, 'socialaccount_set') and request.user.socialaccount_set.exists()
                
                # Handle different verification statuses
                if profile.verification_status == 'not_submitted':
                    if is_social:
                        messages.warning(request, 'Please complete identity verification to continue.')
                    else:
                        messages.warning(request, 'Identity verification required to access features.')
                    return redirect('verification')
                    
                elif profile.verification_status == 'pending':
                    messages.info(request, 'Your verification is under review. Please wait for admin approval.')
                    return redirect('verification')
                    
                elif profile.verification_status == 'rejected':
                    messages.error(request, 'Your verification was rejected. Please submit valid documents.')
                    return redirect('verification')
                    
                elif profile.verification_status != 'verified':
                    messages.error(request, 'Invalid verification status. Please contact support.')
                    return redirect('verification')
                    
            except UserProfile.DoesNotExist:
                messages.warning(request, 'Please complete your profile verification.')
                return redirect('verification')

        # Allow access to non-protected URLs without verification
        return self.get_response(request)