# trips/context_processors.py

def trip_counts(request):
    """
    Context processor to add common counts to all templates
    """
    if request.user.is_authenticated:
        try:
            from trips.models import TravelPlan, TripParticipant, Payment
            
            user_plans_count = TravelPlan.objects.filter(user=request.user).count()
            participations_count = TripParticipant.objects.filter(user=request.user).count()
            total_trips_count = user_plans_count + participations_count
            
            
            # Count of user transactions (all statuses)
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