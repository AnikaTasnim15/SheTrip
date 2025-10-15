from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def verification_required(view_func):
    """
    Decorator to check if user is verified before accessing a view
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Allow superusers/staff
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        try:
            profile = request.user.userprofile
            
            # Check verification status
            if profile.verification_status == 'not_submitted':
                messages.warning(
                    request,
                    'Please complete your identity verification to access this feature.'
                )
                return redirect('verification')
            
            elif profile.verification_status == 'pending':
                messages.info(
                    request,
                    'Your verification is under review. Please wait for admin approval.'
                )
                return redirect('verification')
            
            elif profile.verification_status == 'rejected':
                messages.error(
                    request,
                    'Your verification was rejected. Please resubmit with valid documents.'
                )
                return redirect('verification')
            
            elif profile.verification_status == 'verified':
                # User is verified, allow access
                return view_func(request, *args, **kwargs)
            
        except Exception:
            messages.warning(
                request,
                'Please complete your verification to continue.'
            )
            return redirect('verification')
    
    return wrapper