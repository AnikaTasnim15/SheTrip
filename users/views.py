from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import LoginForm, UserProfileEditForm
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.urls import reverse
from datetime import date
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.http import JsonResponse
import json
from django.conf import settings

def set_jwt_cookies(response, user):
    """Helper function to set JWT tokens in httpOnly cookies"""
    refresh = RefreshToken.for_user(user)
    
    # Set cookies
    response.set_cookie(
        key='shetrip-auth',
        value=str(refresh.access_token),
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite='Lax',
        max_age=3600,  # 1 hour
    )
    
    response.set_cookie(
        key='shetrip-refresh',
        value=str(refresh),
        httponly=True,
        secure=False,
        samesite='Lax',
        max_age=7776000,  # 90 days
    )
    
    return response
@never_cache
def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if input is email or username
        user = None
        if '@' in username_or_email:
            # Try to find user by email
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            # Authenticate with username
            user = authenticate(request, username=username_or_email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Create response
            response = redirect('dashboard')
            
            # Set JWT tokens in cookies
            response = set_jwt_cookies(response, user)
            
            # Set session expiry
            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(7776000)

            messages.success(request, 'You have successfully logged in.')
            return response
        else:
            messages.error(request, 'Invalid username/email or password.')
            return render(request, 'users/login.html')
    
    return render(request, 'users/login.html')


def logout_view(request):

    # Clear JWT cookies
    response = redirect('login')
    response.delete_cookie('shetrip-auth')
    response.delete_cookie('shetrip-refresh')

    
    storage = messages.get_messages(request)
    storage.used = True

    logout(request)
    messages.info(request, 'You have been logged out.')
    return response


def register_view(request):
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/register.html')

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = password1
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken. Please choose another.')
            return render(request, 'users/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please use another email.')
            return render(request, 'users/register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        UserProfile.objects.create(
            user=user,
            age=request.POST.get('age'),
            phone=request.POST.get('phone', ''),
            city=request.POST.get('city'),
            country=request.POST.get('country'),
            occupation=request.POST.get('occupation', ''),
            languages=request.POST.get('languages', ''),
            travel_style=request.POST.get('travel_style'),
            accommodation=','.join(request.POST.getlist('accommodation')),
            interests=','.join(request.POST.getlist('interests')),
            dream_destinations=request.POST.get('dream_destinations', ''),
            bio=request.POST.get('bio', ''),
            profile_picture=request.FILES.get('profile_picture')
        )

        messages.success(request, "Account created successfully!")
        return redirect('login')

    return render(request, 'users/register.html')


def home_view(request):
    return render(request, 'users/home.html')


@login_required 
def dashboard_view(request):
    """Enhanced dashboard view with verification status check"""
    if request.user.is_superuser:
        return redirect('admin:index')
    
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=request.user,
            age=0,
            verification_status='not_submitted'
        )

    # Show verification status in dashboard
    context = {
        'profile': profile,
        'verification_required': not profile.is_verified,
        'is_social_user': hasattr(request.user, 'socialaccount_set') and request.user.socialaccount_set.exists()
    }

    return render(request, 'users/dashboard.html', context)


@login_required
def edit_profile_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        
        if form.is_valid():
            # Update User model fields
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
             # Handle cropped image
            cropped_image_data = request.POST.get('cropped_image')
            if cropped_image_data:
                import base64
                from django.core.files.base import ContentFile
                import uuid
                
                # Decode base64 image
                format, imgstr = cropped_image_data.split(';base64,')
                ext = format.split('/')[-1]
                
                # Create file
                data = ContentFile(base64.b64decode(imgstr), name=f'profile_{uuid.uuid4()}.{ext}')
                if profile:
                    profile.profile_picture = data
                else:
                    # Create new profile with required fields from form
                    profile = form.save(commit=False)
                    profile.user = user
                    profile.profile_picture = data
                    profile.save()
                    messages.success(request, 'Profile created successfully!')
                    return redirect('dashboard')

            # Update UserProfile
            form.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileEditForm(instance=profile, user=request.user)
    
    return render(request, 'users/edit_profile.html', {'form': form, 'profile': profile})



class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        """Custom password reset with direct email sending"""
        from django.contrib.auth.models import User
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.contrib import messages
        
        email = form.cleaned_data.get('email')
        
        # Find active users with this email
        users = User.objects.filter(email=email, is_active=True)
        
        # If no user found, still show success page (security feature)
        if not users.exists():
            messages.error(
                self.request, 
                f'No account found with email: {email}. Please check your email or register a new account.'
            )
            return redirect('register')
        
        # Send reset email to each user (typically just one)
        for user in users:
            # Generate secure token and UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build email context
            context = {
                'email': user.email,
                'domain': self.request.get_host(),
                'site_name': 'SheTrip',
                'uid': uid,
                'user': user,
                'token': token,
                'protocol': 'https' if self.request.is_secure() else 'http',
            }
            
            # Render email templates
            subject = render_to_string(self.subject_template_name, context)
            subject = ''.join(subject.splitlines())  # Remove newlines
            body = render_to_string(self.email_template_name, context)
            
            # Send email
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                print(f"✅ Password reset email sent to {user.email}")
            except Exception as e:
                # Log error but don't expose to user
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Password reset email failed: {e}")
                messages.error(
                    self.request, 
                    '❌ Failed to send email. Please try again later.'
                )
                return redirect('password_reset')
                # Still redirect to success page (security)
        
        # Store email for success page
        if email:
            self.request.session['reset_email'] = email
            
            messages.success(
            self.request, 
            f'✅ Password reset instructions sent to {email}'
            )
        # Redirect to success page
        return redirect(self.success_url)


def password_reset_done_view(request):
    
    reset_email = request.session.get('reset_email', '')
    
    # Clear session data after displaying
    
    if 'reset_email' in request.session:
        del request.session['reset_email']
    
    context = {

        'reset_email': reset_email
    }
    return render(request, 'users/password_reset_done.html', context)


@login_required
def verification_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        nid_front = request.FILES.get('nid_front')
        nid_back = request.FILES.get('nid_back')
        
        if nid_front and nid_back:
            from django.utils import timezone
            
            profile.nid_front = nid_front
            profile.nid_back = nid_back
            profile.verification_status = 'pending'
            profile.submitted_at = timezone.now()
            profile.save()
            
            messages.success(request, 'Verification documents submitted successfully! Admin will review soon.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please upload both front and back of your NID.')
    
    context = {
        'profile': profile,
    }
    return render(request, 'users/verification.html', context)