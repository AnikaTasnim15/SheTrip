# trips/context_processors.py

def trip_counts(request):
    """
    Context processor to add common counts to all templates
    """
    if request.user.is_authenticated:
        try:
            from trips.models import TravelPlan, TripParticipant, Payment
            
            # Count user's travel plans
            user_plans_count = TravelPlan.objects.filter(user=request.user).count()
            
            # Count trips user is participating in (organized trips joined)
            participations_count = TripParticipant.objects.filter(user=request.user).count()
            
            # Total trips = organized trips the user has joined
            total_trips_count = participations_count
            
            # Count of user payments
            user_payments_count = Payment.objects.filter(user=request.user).count()

            return {
                'total_trips_count': total_trips_count,
                'user_payments_count': user_payments_count,
                'user_plans_count': user_plans_count,
            }
        except Exception:
            return {
                'total_trips_count': 0,
                'user_payments_count': 0,
                'user_plans_count': 0,
            }

    return {
        'total_trips_count': 0,
        'user_payments_count': 0,
        'user_plans_count': 0,
    }