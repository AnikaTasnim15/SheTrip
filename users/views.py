from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import LoginForm
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'You have successfully logged in.')
            return redirect('dashboard')  # change 'home' to your homepage URL name
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')  # redirect to login page after logout

def register_view(request):
    if request.method == 'POST':

        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/register.html')
        
        # Create user
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = password1
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken. Please choose another.')
            return render(request, 'users/register.html')
        
        # Check if email already exists
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
        
        # Create profile
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
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    return render(request, 'users/dashboard.html', {'profile': profile})