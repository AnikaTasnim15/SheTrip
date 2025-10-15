from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import TravelPlan, OrganizedTrip, TripParticipant, TravelMatch
from .forms import TravelPlanForm, TripSearchForm, JoinTripForm
from datetime import date
from users.models import UserProfile
from users.decorators import verification_required

@login_required
@verification_required
def my_trips_view(request):
    """Display user's travel plans and trip participations"""
    
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
  
    
    user_plans = TravelPlan.objects.filter(user=request.user)
    
    # Get trips user is participating in
    participations = TripParticipant.objects.filter(user=request.user).select_related('trip')

    total_co_travelers = sum(
        p.trip.total_participants - 1  # -1 to exclude the user themselves
        for p in participations 
        if p.trip
    )
    
    # Get matched buddies count
    user_plan_ids = user_plans.values_list('plan_id', flat=True)
    matched_buddies = TravelMatch.objects.filter(
        Q(travel_plan_1_id__in=user_plan_ids) | Q(travel_plan_2_id__in=user_plan_ids),
        match_status='accepted'
    ).count()
    
    # Get next upcoming trip
    next_trip = user_plans.filter(
        start_date__gte=date.today(),
        is_active=True
    ).order_by('start_date').first()

      # Get next organized trip departure
    next_organized_trip = participations.filter(
        trip__departure_time__gte=date.today()
    ).order_by('trip__departure_time').first()
    
    # Get past trips count
    past_trips = participations.filter(
        trip__departure_time__lt=date.today()
    )

     # Calculate past trips statistics
    completed_trips_count = past_trips.count()
    places_visited = past_trips.values('trip__destination').distinct().count()
    
    # Count total travel buddies met (sum of all participants from past trips minus self)
    travel_buddies_met = sum(
        p.trip.total_participants - 1
        for p in past_trips
        if p.trip
    )


    context = {
        'user_plans': user_plans,
        'participations': participations,
        'total_co_travelers': total_co_travelers,
        'matched_buddies': matched_buddies,
        'next_trip': next_trip,
        'next_organized_trip': next_organized_trip,
        'past_trips': past_trips,
        'completed_trips_count': completed_trips_count,
        'places_visited': places_visited,
        'travel_buddies_met': travel_buddies_met,
        'profile': profile, 
        'user': request.user,
    }
    return render(request, 'trips/my_trips.html', context)


@login_required
@verification_required
def create_travel_plan_view(request):
    """Create a new travel plan"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

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

    context = {
        'form': form,
        'profile': profile, 
        'user': request.user,
    }
    
    return render(request, 'trips/create_plan.html', context)


@login_required
@verification_required
def edit_travel_plan_view(request, plan_id):
    """Edit an existing travel plan"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

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
    
    context = {
        'form': form,
        'travel_plan': travel_plan,
        'profile': profile,
        'user': request.user,
    }

    return render(request, 'trips/edit_plan.html', context)


@login_required
@verification_required
def delete_travel_plan_view(request, plan_id):
    """Delete a travel plan"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    travel_plan = get_object_or_404(TravelPlan, plan_id=plan_id, user=request.user)
    
    if request.method == 'POST':
        travel_plan.delete()
        messages.success(request, 'Travel plan deleted successfully.')
        return redirect('my_trips')
    
    context = {
        'travel_plan': travel_plan,
        'profile': profile,
        'user': request.user,
    } 
    
    return render(request, 'trips/delete_plan_confirm.html', context)


@login_required
@verification_required
def find_travel_buddies_view(request):
    """Search for compatible travel plans"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    
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
    travel_plans = travel_plans.filter(start_date__gte=date.today()).select_related('user', 'user__userprofile')
    
    context = {
        'form': form,
        'travel_plans': travel_plans,
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'trips/find_buddies.html', context)


@login_required
@verification_required
def travel_plan_detail_view(request, plan_id):
    """View details of a specific travel plan"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    
    travel_plan = get_object_or_404(TravelPlan.objects.select_related('user', 'user__userprofile'), plan_id=plan_id)
    
    
    # Check if there's a match between current user's plans and this plan
    user_plans = TravelPlan.objects.filter(user=request.user, is_active=True)
    potential_matches = []
    
    for user_plan in user_plans:
        # Simple compatibility check
        if (user_plan.destination.lower() == travel_plan.destination.lower() and
            user_plan.budget_range == travel_plan.budget_range):
            potential_matches.append(user_plan)

    # Check if there's already a match
    existing_match = TravelMatch.objects.filter(
        Q(travel_plan_1=travel_plan, travel_plan_2__in=user_plans) |
        Q(travel_plan_2=travel_plan, travel_plan_1__in=user_plans)
    ).first()

    context = {
        'travel_plan': travel_plan,
        'potential_matches': potential_matches,
        'existing_match': existing_match,
        'is_owner': travel_plan.user == request.user,
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'trips/plan_detail.html', context)


@login_required
@verification_required
def organized_trips_view(request):
    """View all available organized trips"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    # Get active organized trips with available slots
    organized_trips = OrganizedTrip.objects.filter(
        trip_status__in=['open', 'confirmed']
    ).select_related('driver').order_by('departure_time')
    
    # Check which trips the user has already joined
    user_trip_ids = TripParticipant.objects.filter(
        user=request.user
    ).values_list('trip_id', flat=True)
    
    total_trips = organized_trips.count()
    available_trips = sum(1 for trip in organized_trips if trip.available_slots() > 0)
  

    context = {
        'organized_trips': organized_trips,
        'user_trip_ids': list(user_trip_ids),
        'total_trips': total_trips,
        'available_trips': available_trips,
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'trips/organized_trips.html', context)


@login_required
@verification_required
def organized_trip_detail_view(request, trip_id):
    """View details of an organized trip"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    trip = get_object_or_404(
         OrganizedTrip.objects.select_related('driver', 'travel_plan'),
         trip_id=trip_id
    )
    
    # Check if user has already joined
    is_participant = TripParticipant.objects.filter(
        trip=trip,
        user=request.user
    ).exists()
    
    # Get participants
    participants = TripParticipant.objects.filter(trip=trip).select_related('user', 'user__userprofile')

    
    # Get user's participation details if they're a participant
    user_participation = None
    if is_participant:
        user_participation = participants.filter(user=request.user).first()
    

    context = {
        'trip': trip,
        'is_participant': is_participant,
        'user_participation': user_participation,
        'participants': participants,
        'available_slots': trip.available_slots(),
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'trips/organized_trip_detail.html', context)


@login_required
@verification_required
def join_organized_trip_view(request, trip_id):
    """Join an organized trip"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

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
        'available_slots': trip.available_slots(),
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'trips/join_trip.html', context)


@login_required
@verification_required
def leave_organized_trip_view(request, trip_id):
    """Leave an organized trip"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    
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
    
    context = {
        'trip': trip,
        'profile': profile,
        'participant': participant,
        'user': request.user,
    }
    return render(request, 'trips/leave_trip_confirm.html', context)
        
    
    


@login_required
@verification_required
def trip_matches_view(request):
    """View travel plan matches"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    # Get matches where user is either plan_1 or plan_2
    user_plans = TravelPlan.objects.filter(user=request.user)
    
    matches = TravelMatch.objects.filter(
        Q(travel_plan_1__in=user_plans) | Q(travel_plan_2__in=user_plans),
        match_status='pending'
    ).select_related('travel_plan_1', 'travel_plan_2', 'travel_plan_1__user','travel_plan_1__user__userprofile', 'travel_plan_2__user',  'travel_plan_2__user__userprofile')


    
    # Get accepted matches count
    accepted_matches = TravelMatch.objects.filter(
        Q(travel_plan_1__in=user_plans) | Q(travel_plan_2__in=user_plans),
        match_status='accepted'
    ).count()
    

    context = {
        'matches': matches,
        'accepted_matches': accepted_matches,
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'trips/matches.html', context)