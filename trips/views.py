from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import TravelPlan, OrganizedTrip, TripParticipant, TravelMatch
from .forms import TravelPlanForm, TripSearchForm, JoinTripForm
from datetime import date

@login_required
def my_trips_view(request):
    """Display user's travel plans and trip participations"""
    user_plans = TravelPlan.objects.filter(user=request.user)
    
    # Get trips user is participating in
    participations = TripParticipant.objects.filter(user=request.user).select_related('trip')
    
    context = {
        'user_plans': user_plans,
        'participations': participations,
    }
    return render(request, 'trips/my_trips.html', context)


@login_required
def create_travel_plan_view(request):
    """Create a new travel plan"""
    if request.method == 'POST':
        form = TravelPlanForm(request.POST)
        if form.is_valid():
            travel_plan = form.save(commit=False)
            travel_plan.user = request.user
            travel_plan.save()
            messages.success(request, 'Travel plan created successfully! We will match you with compatible travelers.')
            return redirect('my_trips')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TravelPlanForm()
    
    return render(request, 'trips/create_plan.html', {'form': form})


@login_required
def edit_travel_plan_view(request, plan_id):
    """Edit an existing travel plan"""
    travel_plan = get_object_or_404(TravelPlan, plan_id=plan_id, user=request.user)
    
    if request.method == 'POST':
        form = TravelPlanForm(request.POST, instance=travel_plan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Travel plan updated successfully!')
            return redirect('my_trips')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TravelPlanForm(instance=travel_plan)
    
    return render(request, 'trips/edit_plan.html', {'form': form, 'travel_plan': travel_plan})


@login_required
def delete_travel_plan_view(request, plan_id):
    """Delete a travel plan"""
    travel_plan = get_object_or_404(TravelPlan, plan_id=plan_id, user=request.user)
    
    if request.method == 'POST':
        travel_plan.delete()
        messages.success(request, 'Travel plan deleted successfully.')
        return redirect('my_trips')
    
    return render(request, 'trips/delete_plan_confirm.html', {'travel_plan': travel_plan})


@login_required
def find_travel_buddies_view(request):
    """Search for compatible travel plans"""
    form = TripSearchForm(request.GET or None)
    travel_plans = TravelPlan.objects.filter(is_active=True).exclude(user=request.user)
    
    # Filter by search criteria
    if form.is_valid():
        destination = form.cleaned_data.get('destination')
        start_date = form.cleaned_data.get('start_date')
        budget_range = form.cleaned_data.get('budget_range')
        purpose = form.cleaned_data.get('purpose')
        
        if destination:
            travel_plans = travel_plans.filter(destination__icontains=destination)
        if start_date:
            travel_plans = travel_plans.filter(start_date__gte=start_date)
        if budget_range:
            travel_plans = travel_plans.filter(budget_range=budget_range)
        if purpose:
            travel_plans = travel_plans.filter(purpose=purpose)
    
    # Only show future trips
    travel_plans = travel_plans.filter(start_date__gte=date.today())
    
    context = {
        'form': form,
        'travel_plans': travel_plans,
    }
    return render(request, 'trips/find_buddies.html', context)


@login_required
def travel_plan_detail_view(request, plan_id):
    """View details of a specific travel plan"""
    travel_plan = get_object_or_404(TravelPlan, plan_id=plan_id)
    
    # Check if there's a match between current user's plans and this plan
    user_plans = TravelPlan.objects.filter(user=request.user, is_active=True)
    potential_matches = []
    
    for user_plan in user_plans:
        # Simple compatibility check
        if (user_plan.destination.lower() == travel_plan.destination.lower() and
            user_plan.budget_range == travel_plan.budget_range):
            potential_matches.append(user_plan)
    
    context = {
        'travel_plan': travel_plan,
        'potential_matches': potential_matches,
        'is_owner': travel_plan.user == request.user,
    }
    return render(request, 'trips/plan_detail.html', context)


@login_required
def organized_trips_view(request):
    """View all available organized trips"""
    # Get active organized trips with available slots
    organized_trips = OrganizedTrip.objects.filter(
        trip_status__in=['open', 'confirmed']
    ).select_related('driver').order_by('departure_time')
    
    # Check which trips the user has already joined
    user_trip_ids = TripParticipant.objects.filter(
        user=request.user
    ).values_list('trip_id', flat=True)
    
    context = {
        'organized_trips': organized_trips,
        'user_trip_ids': list(user_trip_ids),
    }
    return render(request, 'trips/organized_trips.html', context)


@login_required
def organized_trip_detail_view(request, trip_id):
    """View details of an organized trip"""
    trip = get_object_or_404(OrganizedTrip, trip_id=trip_id)
    
    # Check if user has already joined
    is_participant = TripParticipant.objects.filter(
        trip=trip,
        user=request.user
    ).exists()
    
    # Get participants
    participants = TripParticipant.objects.filter(trip=trip).select_related('user')
    
    context = {
        'trip': trip,
        'is_participant': is_participant,
        'participants': participants,
        'available_slots': trip.available_slots(),
    }
    return render(request, 'trips/organized_trip_detail.html', context)


@login_required
def join_organized_trip_view(request, trip_id):
    """Join an organized trip"""
    trip = get_object_or_404(OrganizedTrip, trip_id=trip_id)
    
    # Check if already joined
    if TripParticipant.objects.filter(trip=trip, user=request.user).exists():
        messages.warning(request, 'You have already joined this trip.')
        return redirect('organized_trip_detail', trip_id=trip_id)
    
    # Check if trip is open and has slots
    if trip.trip_status not in ['open', 'confirmed']:
        messages.error(request, 'This trip is not open for registration.')
        return redirect('organized_trip_detail', trip_id=trip_id)
    
    if trip.available_slots() <= 0:
        messages.error(request, 'This trip is full.')
        return redirect('organized_trip_detail', trip_id=trip_id)
    
    if request.method == 'POST':
        form = JoinTripForm(request.POST)
        if form.is_valid():
            # Create participant record
            participant = TripParticipant.objects.create(
                trip=trip,
                user=request.user,
                amount_paid=0,
                commission_charged=trip.platform_commission,
                payment_status='pending'
            )
            
            # Update total participants
            trip.total_participants += 1
            trip.save()
            
            messages.success(request, 'You have successfully joined the trip! Please complete payment.')
            return redirect('organized_trip_detail', trip_id=trip_id)
    else:
        form = JoinTripForm()
    
    context = {
        'trip': trip,
        'form': form,
    }
    return render(request, 'trips/join_trip.html', context)


@login_required
def leave_organized_trip_view(request, trip_id):
    """Leave an organized trip"""
    trip = get_object_or_404(OrganizedTrip, trip_id=trip_id)
    participant = get_object_or_404(TripParticipant, trip=trip, user=request.user)
    
    if request.method == 'POST':
        # Check if payment was made
        if participant.payment_status == 'paid':
            messages.warning(request, 'Please contact admin for refund before leaving.')
            return redirect('organized_trip_detail', trip_id=trip_id)
        
        # Delete participant record
        participant.delete()
        
        # Update total participants
        trip.total_participants -= 1
        trip.save()
        
        messages.success(request, 'You have left the trip.')
        return redirect('organized_trips')
    
    return render(request, 'trips/leave_trip_confirm.html', {'trip': trip})


@login_required
def trip_matches_view(request):
    """View travel plan matches"""
    # Get matches where user is either plan_1 or plan_2
    user_plans = TravelPlan.objects.filter(user=request.user)
    
    matches = TravelMatch.objects.filter(
        Q(travel_plan_1__in=user_plans) | Q(travel_plan_2__in=user_plans),
        match_status='pending'
    ).select_related('travel_plan_1', 'travel_plan_2', 'travel_plan_1__user', 'travel_plan_2__user')
    
    context = {
        'matches': matches,
    }
    return render(request, 'trips/matches.html', context)