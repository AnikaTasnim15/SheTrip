from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import LoginForm, UserProfileEditForm
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


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
            messages.success(request, 'You have successfully logged in.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username/email or password.')
            return render(request, 'users/login.html')
    
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


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
    """
    Enhanced dashboard view with complete user and trip information
    """
    if request.user.is_superuser:  # or request.user.is_staff
        return redirect('admin:index')  # redirect admin to admin panel
    
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    # Prepare context data for the dashboard
    context = {
        'profile': profile,
        'user': request.user,
        # These will be populated once trip models are created
        'upcoming_trips_count': 0,
        'completed_trips_count': 0,
        'travel_buddies_count': 0,
        'user_rating': 'New',
        'upcoming_trips': [],
        'recent_activities': [
            {
                'icon': '🎉',
                'title': 'Welcome to SheTrip!',
                'description': 'Account created successfully',
                'bg_color': '#ddd6fe'
            }
        ]
    }

    return render(request, 'users/dashboard.html', context)


@login_required
def edit_profile_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        
        if form.is_valid():
            # Update User model fields
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Update UserProfile
            form.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileEditForm(instance=profile, user=request.user)
    
    return render(request, 'users/edit_profile.html', {'form': form, 'profile': profile})