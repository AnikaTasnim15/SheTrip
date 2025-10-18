from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from trips.models import TravelPlan, OrganizedTrip, TripParticipant, TravelPlanInterest, Payment


class Command(BaseCommand):
    help = "Auto-close TravelPlans after 5 minutes, approve when 2 paid, and update OrganizedTrip statuses."

    def handle(self, *args, **options):
        now = timezone.now()

        # 1. Close open plans past join_deadline (5-minute window)
        closed_count = TravelPlan.objects.filter(status='open', join_deadline__lt=now).update(status='closed')
        if closed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'{closed_count} plans auto-closed after 5-minute join window'))

        # 2. Reject finalized plans where payment deadline passed with insufficient payments
        for plan in TravelPlan.objects.filter(status='finalized', payment_deadline__lt=now, organized_trip__isnull=True):
            # Count users who agreed AND paid
            agreed_users = TravelPlanInterest.objects.filter(plan=plan, agreed=True)
            paid_count = 0
            
            for interest in agreed_users:
                # Check if payment exists and is completed (payments made after plan finalization)
                payment_exists = Payment.objects.filter(
                    user=interest.user,
                    payment_status='completed',
                    payment_date__gte=plan.updated_at  # Only count payments after finalization
                ).exists()
                
                if payment_exists:
                    paid_count += 1
            
            if paid_count < 2:  # Less than 2 paid participants
                plan.status = 'rejected'
                plan.save(update_fields=['status'])
                self.stdout.write(self.style.WARNING(f'Plan {plan.plan_id} rejected - insufficient payments ({paid_count} < 2)'))

        # 3. AUTO-CREATE OrganizedTrip when conditions are met
        for plan in TravelPlan.objects.filter(status='finalized', organized_trip__isnull=True):
            # Count users who agreed AND paid
            agreed_users = TravelPlanInterest.objects.filter(plan=plan, agreed=True)
            paid_count = 0
            paid_users = []
            
            for interest in agreed_users:
                # Check if this user has a completed payment (no trip filter since OrganizedTrip doesn't exist yet)
                payment_exists = Payment.objects.filter(
                    user=interest.user,
                    payment_status='completed',
                    payment_date__gte=plan.updated_at  # Only count payments made after plan was finalized
                ).exists()
                
                if payment_exists:
                    paid_count += 1
                    paid_users.append(interest)
            
            # Create trip when: max participants paid OR payment deadline passed with at least 2 paid
            should_create = (
                paid_count >= plan.max_participants or  
                (plan.payment_deadline and now > plan.payment_deadline and paid_count >= 2)
            )
            
            if should_create:
                # Create OrganizedTrip
                organized_trip = OrganizedTrip.objects.create(
                    travel_plan=plan,
                    trip_name=f"{plan.destination} - {plan.start_date.strftime('%b %d')}",
                    destination=plan.destination,
                    departure_time=plan.start_date,
                    return_time=plan.end_date,
                    total_participants=paid_count,
                    platform_commission=plan.platform_commission or 0,
                    final_cost_per_person=plan.final_cost_per_person or 0,
                    profit_margin=plan.profit_margin or 0,
                    transportation_details=plan.transportation_details or '',
                    accommodation_details=plan.accommodation_details or '',
                    meal_arrangements=plan.meal_arrangements or '',
                    itinerary=plan.itinerary or '',
                    driver=plan.assigned_driver,
                    driver_payment=plan.driver_payment or 0,
                    trip_status='confirmed',
                    base_cost=plan.final_cost_per_person * paid_count,
                )
                
                # Update existing payments to link to OrganizedTrip
                Payment.objects.filter(
                    user__in=[interest.user for interest in paid_users],
                    payment_status='completed',
                    trip__isnull=True,
                    payment_date__gte=plan.updated_at
                ).update(trip=organized_trip)
                
                # Create TripParticipant entries for all users who paid
                for interest in paid_users:
                    TripParticipant.objects.get_or_create(
                        trip=organized_trip,
                        user=interest.user,
                        defaults={
                            'payment_status': 'paid',
                            'amount_paid': plan.final_cost_per_person,
                            'commission_charged': plan.platform_commission or 0,
                        }
                    )
                
                plan.status = 'approved'
                plan.save(update_fields=['status'])
                self.stdout.write(self.style.SUCCESS(f'OrganizedTrip {organized_trip.trip_id} created for plan {plan.plan_id} with {paid_count} participants'))
        
        # 4. Move confirmed trips to ongoing/completed based on dates
        ongoing_count = 0
        completed_count = 0
        
        for trip in OrganizedTrip.objects.filter(trip_status='confirmed'):
            if trip.departure_time <= now < trip.return_time:
                trip.trip_status = 'ongoing'
                trip.save(update_fields=['trip_status'])
                ongoing_count += 1
            elif trip.return_time <= now:
                trip.trip_status = 'completed'
                trip.save(update_fields=['trip_status'])
                completed_count += 1
        
        if ongoing_count > 0:
            self.stdout.write(self.style.SUCCESS(f'{ongoing_count} trips moved to ongoing status'))
        
        if completed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'{completed_count} trips moved to completed status'))

        self.stdout.write(self.style.SUCCESS(' Auto update completed successfully.'))