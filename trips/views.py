from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import TravelPlan, OrganizedTrip, TripParticipant, TravelMatch, TravelPlanInterest
from .forms import TravelPlanForm, TripSearchForm, JoinTripForm
from datetime import date, date, timedelta, datetime
from users.models import UserProfile
from users.decorators import verification_required
from django.utils import timezone


@login_required
@verification_required
def my_trips_view(request):
    """Display user's travel plans and trip participations"""
    
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
  
    
    now = timezone.now()
    today = timezone.localdate()  
    
    user_plans = TravelPlan.objects.filter(user=request.user)
    
    
    participations = TripParticipant.objects.filter(user=request.user).select_related('trip')

    total_co_travelers = sum(
        p.trip.total_participants - 1  
        for p in participations 
        if p.trip
    )
    
    active_participations = participations.filter(
        trip__departure_time__lte=now,
        trip__return_time__gte=now
    ) 
    
    user_plan_ids = user_plans.values_list('plan_id', flat=True)
    matched_buddies = TravelMatch.objects.filter(
        Q(travel_plan_1_id__in=user_plan_ids) | Q(travel_plan_2_id__in=user_plan_ids),
        match_status='accepted'
    ).count()
    
    
    next_trip = user_plans.filter(
        start_date__gte=today,
        is_active=True
    ).order_by('start_date').first()

    
    next_organized_trip = participations.filter(
        trip__departure_time__gte=now,
        payment_status='paid'  
    ).order_by('trip__departure_time').first()
    
    
    past_trips = participations.filter(
        trip__return_time__lt=now
    )

    
    completed_trips_count = past_trips.count()
    places_visited = past_trips.values('trip__destination').distinct().count()
    

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
        'plan_interest_counts': {
            plan.plan_id: TravelPlanInterest.objects.filter(plan=plan).count()
            for plan in user_plans
        },
        'profile': profile, 
        'active_participations': active_participations,
        'user': request.user,
        'today': today,  
        'now': now,  
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
            # DEBUG: Print form errors
            print("FORM ERRORS:", form.errors)
            print("FORM ERRORS DICT:", form.errors.as_data())
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
    # Show only active and still-open (not past join_deadline) plans
    travel_plans = TravelPlan.objects.filter(
        is_active=True,
        status__in=['open', 'closed', 'finalized'],
    )

    
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
    travel_plans = travel_plans.filter(start_date__gte=date.today()).select_related('user', 'user__userprofile').order_by('-created_at')
    
    
    
    context = {
        'form': form,
        'travel_plans': travel_plans,
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'trips/find_buddies.html', context)


@login_required

def travel_plan_detail_view(request, plan_id):
    """View details - ONLY FIX: Safe organized_trip check"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    
    travel_plan = get_object_or_404(
        TravelPlan.objects.select_related('user', 'user__userprofile'), 
        plan_id=plan_id
    )
    
    interested_users = TravelPlanInterest.objects.filter(
        plan=travel_plan
    ).select_related('user', 'user__userprofile')
    
    # Interest state for current user
    user_interest = None
    user_interested = False
    if request.user != travel_plan.user:
        user_interest = TravelPlanInterest.objects.filter(
            plan=travel_plan, 
            user=request.user
        ).first()
        user_interested = user_interest is not None
    
    # ONLY FIX: Check if user has paid - use getattr to avoid error
    user_paid = False
    if travel_plan.status == 'finalized':
        from trips.models import Payment
        organized_trip = getattr(travel_plan, 'organized_trip', None)
        if organized_trip:
            user_paid = Payment.objects.filter(
                user=request.user,
                trip=organized_trip,
                payment_status='completed'
            ).exists()

    context = {
        'travel_plan': travel_plan,
        'is_owner': travel_plan.user == request.user,
        'user_interested': user_interested,
        'interest_count': interested_users.count(),
        'interested_users': interested_users,
        'profile': profile,
        'user': request.user,
        'user_paid': user_paid,
    }
    
    return render(request, 'trips/plan_detail.html', context)
    
    
@verification_required
def express_interest_view(request, plan_id):
    """User expresses interest in a TravelPlan within 1-week window (no payment yet)"""
    plan = get_object_or_404(TravelPlan, plan_id=plan_id, is_active=True)

    if plan.user_id == request.user.id:
        messages.error(request, 'You cannot join your own plan.')
        return redirect('travel_plan_detail', plan_id=plan_id)

    if not plan.is_join_window_open:
        messages.error(request, 'This plan is closed for new interests.')
        return redirect('travel_plan_detail', plan_id=plan_id)

    TravelPlanInterest.objects.get_or_create(plan=plan, user=request.user)
    messages.success(request, 'Interest recorded! You will see updates here.')
    return redirect('travel_plan_detail', plan_id=plan_id)


@login_required

def withdraw_interest_view(request, plan_id):
    """User withdraws interest before admin finalization"""
    plan = get_object_or_404(TravelPlan, plan_id=plan_id)
    interest = TravelPlanInterest.objects.filter(plan=plan, user=request.user).first()
    if not interest:
        messages.info(request, 'You have not joined this plan.')
        return redirect('travel_plan_detail', plan_id=plan_id)
    interest.delete()
    messages.success(request, 'You have withdrawn your interest.')
    return redirect('travel_plan_detail', plan_id=plan_id)


@login_required
@verification_required
def organized_trips_view(request):
    """View only organized trips the user has joined"""

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    # Get only trips the user has joined
    user_participations = TripParticipant.objects.filter(
        user=request.user
    ).select_related('trip', 'trip__driver').order_by('trip__departure_time')
    
    # Extract trips from participations
    organized_trips = [p.trip for p in user_participations]
    
    # Already filtered to user's trips
    user_trip_ids = [trip.trip_id for trip in organized_trips]
    
    total_trips = len(organized_trips)
    available_trips = sum(1 for trip in organized_trips if trip.available_slots() > 0)

    context = {
        'organized_trips': organized_trips,
        'user_trip_ids': user_trip_ids,
        'total_trips': total_trips,
        'available_trips': available_trips,
        'total_participants': sum(trip.total_participants for trip in organized_trips),
        'unique_destinations': len(set(trip.destination for trip in organized_trips)),
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'trips/organized_trips.html', context)


@login_required
def organized_trip_detail_view(request, trip_id):
    """View trip detail - ADD refund deadline calculation"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    trip = get_object_or_404(
        OrganizedTrip.objects.select_related('driver', 'travel_plan'),
        trip_id=trip_id
    )
    
    # Check if user is participant
    user_participation = TripParticipant.objects.filter(
        trip=trip,
        user=request.user
    ).first()
    
    # Get all participants
    participants = TripParticipant.objects.filter(trip=trip).select_related('user', 'user__userprofile')
    
    # ADDED: Calculate refund eligibility (5-minute window)
    can_refund = False
    refund_deadline = None
    
    if user_participation and user_participation.payment_status == 'paid':
        from trips.models import Payment
        latest_payment = Payment.objects.filter(
            user=request.user,
            trip=trip,
            payment_status='completed'
        ).order_by('-payment_date').first()
        
        if latest_payment:
            refund_deadline = latest_payment.payment_date + timedelta(minutes=5)
            can_refund = timezone.now() < refund_deadline

    context = {
        'trip': trip,
        'user_participation': user_participation,
        'participants': participants,
        'available_slots': trip.available_slots(),
        'profile': profile,
        'user': request.user,
        'can_refund': can_refund,
        'refund_deadline': refund_deadline,
    }
    return render(request, 'trips/organized_trip_detail.html', context)


@login_required
def join_organized_trip_view(request, trip_id):
    """Join organized trip - CREATE TripParticipant and redirect to payment"""
    
    # ADD DEBUGGING
    print(f"\n=== JOIN TRIP VIEW DEBUG ===")
    print(f"Method: {request.method}")
    print(f"Trip ID: {trip_id}")
    print(f"User: {request.user}")
    print(f"POST data: {request.POST}")
    
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    trip = get_object_or_404(OrganizedTrip, trip_id=trip_id)
    
    # Check if already joined
    if TripParticipant.objects.filter(trip=trip, user=request.user).exists():
        messages.warning(request, 'You have already joined this trip.')
        return redirect('organized_trip_detail', trip_id=trip_id)
    
    # Check if trip is open
    if trip.trip_status not in ['open', 'confirmed', 'planning']:
        messages.error(request, 'This trip is not open for registration.')
        return redirect('organized_trip_detail', trip_id=trip_id)
    
    if trip.available_slots() <= 0:
        messages.error(request, 'This trip is full.')
        return redirect('organized_trip_detail', trip_id=trip_id)
    
    if request.method == 'POST':
        print("POST method detected - processing form")
        form = JoinTripForm(request.POST)
        
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            print(f"Form errors dict: {form.errors.as_data()}")
        
        if form.is_valid():
            print("Creating participant...")
            # CREATE PARTICIPANT with pending payment status
            participant = TripParticipant.objects.create(
                trip=trip,
                user=request.user,
                emergency_contact=form.cleaned_data.get('emergency_contact'),
                special_requirements=form.cleaned_data.get('special_requirements'),
                amount_paid=0,
                payment_status='pending'
            )
            print(f"Participant created: {participant.participant_id}")
            
            # Update total participants
            trip.total_participants += 1
            trip.save()
            print(f"Trip participants updated to: {trip.total_participants}")
            
            messages.success(request, 'Registration complete! Please proceed to payment.')
            
            print(f"Redirecting to trip_payment with trip_id={trip_id}")
            return redirect('trip_payment', trip_id=trip_id)
        else:
            print(f"Form validation FAILED")
            messages.error(request, 'Please correct the errors below.')
    else:
        print("GET method - showing form")
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

def leave_organized_trip_view(request, trip_id):
    """Leave trip - ONLY FIX: Check trip status instead of payment status"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    
    trip = get_object_or_404(OrganizedTrip, trip_id=trip_id)
    participant = get_object_or_404(TripParticipant, trip=trip, user=request.user)
    
    if request.method == 'POST':
        # ONLY CHECK: If trip has already started
        if trip.trip_status in ['ongoing', 'completed']:
            messages.error(request, 'Cannot leave - trip is already underway.')
            return redirect('organized_trip_detail', trip_id=trip_id)
        
        # Delete participant
        participant.delete()
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


def _recalculate_trip_status(trip: OrganizedTrip) -> None:
    """Set trip to confirmed if at least 2 paid participants, else keep status."""
    paid_count = TripParticipant.objects.filter(trip=trip, payment_status='paid').count()
    if paid_count >= 2 and trip.trip_status in ['open', 'planning']:
        trip.trip_status = 'confirmed'
        # Ensure at least 5 minutes prep time (test-friendly)
        min_departure = timezone.now() + timedelta(minutes=5)
        if trip.departure_time < min_departure:
            trip.departure_time = min_departure
        trip.save()


@login_required
def agree_plan_details_view(request, plan_id):
    """User agrees to finalized plan - create OrganizedTrip and redirect to join"""
    from datetime import datetime, time
    
    plan = get_object_or_404(TravelPlan, plan_id=plan_id, status='finalized')
    
    
    is_creator = plan.user == request.user
    
    if not is_creator:
        interest = TravelPlanInterest.objects.filter(
            plan=plan, 
            user=request.user
        ).first()
        
        if not interest:
            messages.error(request, 'You must express interest in the plan first.')
            return redirect('travel_plan_detail', plan_id=plan_id)
    else:
        interest, created = TravelPlanInterest.objects.get_or_create(
            plan=plan,
            user=request.user
        )
    
    
    interest.agreed = True
    interest.agreed_at = timezone.now()
    interest.save()
    
   
    plan.payment_deadline = timezone.now() + timedelta(minutes=5)
    plan.save()
    
    
    departure_naive = datetime.combine(plan.start_date, time(9, 0))  # 9 AM departure
    return_naive = datetime.combine(plan.end_date, time(18, 0))  # 6 PM return
    
    departure_time = timezone.make_aware(departure_naive)
    return_time = timezone.make_aware(return_naive)
    
    
    organized_trip, created = OrganizedTrip.objects.get_or_create(
        travel_plan=plan,
        defaults={
            'trip_name': plan.destination,
            'destination': plan.destination,
            'trip_status': 'planning',
            'base_cost': plan.final_cost_per_person or 0,
            'platform_commission': plan.platform_commission or 0,
            'final_cost_per_person': plan.final_cost_per_person or 0,
            'profit_margin': plan.profit_margin or 0,
            'driver_payment': plan.driver_payment or 0,
            'transportation_details': plan.transportation_details or '',
            'accommodation_details': plan.accommodation_details or '',
            'meal_arrangements': plan.meal_arrangements or '',
            'departure_time': departure_time, 
            'return_time': return_time, 
            'total_participants': 0,
        }
    )
    
    if is_creator:
        messages.success(request, 'You agreed to your plan! Proceeding to join as participant...')
    else:
        messages.success(request, 'You agreed to the plan! Proceeding to join...')
    
    
    return redirect('join_organized_trip', trip_id=organized_trip.trip_id)
@login_required

def initiate_payment_view(request, trip_id):
    messages.info(request, 'Redirecting to payment page...')
    return redirect('trip_payment', trip_id=trip_id)


@login_required

def cancel_payment_view(request, trip_id):
    return redirect('trip_cancel_payment', trip_id=trip_id)