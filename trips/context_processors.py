# trips/context_processors.py

def trip_counts(request):
    """
    Context processor to add trip counts to all templates
    """
    if request.user.is_authenticated:
        try:
            from trips.models import TravelPlan, TripParticipant
            
            user_plans_count = TravelPlan.objects.filter(user=request.user).count()
            participations_count = TripParticipant.objects.filter(user=request.user).count()
            total_trips_count = user_plans_count + participations_count
            
            return {
                'total_trips_count': total_trips_count,
            }
        except Exception:
            return {'total_trips_count': 0}
    
    return {'total_trips_count': 0}