from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from datetime import timedelta
import uuid

from trips.models import OrganizedTrip, TripParticipant, Payment
from users.decorators import verification_required
from .sslcommerz import SSLCommerzPayment


@login_required
@verification_required
def trip_payment_view(request, trip_id):
    """Payment - handles payment submission with SSLCommerz"""
    try:
        profile = request.user.userprofile
    except:
        profile = None
    
    trip = get_object_or_404(OrganizedTrip, trip_id=trip_id)
    
    # Get participant record
    try:
        participant = TripParticipant.objects.get(trip=trip, user=request.user)
    except TripParticipant.DoesNotExist:
        messages.error(request, 'You must join this trip before making payment.')
        return redirect('organized_trip_detail', trip_id=trip_id)
    
    # Check if already paid
    if participant.payment_status == 'paid':
        messages.info(request, 'You have already paid for this trip.')
        return redirect('organized_trip_detail', trip_id=trip_id)
    
    if request.method == 'POST':
        # Generate unique transaction ID
        tran_id = f"TRIP-{trip_id}-USER-{request.user.id}-{uuid.uuid4().hex[:8].upper()}"
        
        # Create pending payment record
        payment = Payment.objects.create(
            trip=trip,
            user=request.user,
            total_amount=trip.final_cost_per_person,
            platform_commission=trip.platform_commission,
            payment_method='sslcommerz',
            payment_status='pending',
            transaction_id=tran_id,
        )
        
        # Initialize SSLCommerz
        sslcz = SSLCommerzPayment()
        
        # Prepare payment data
        payment_data = {
            'total_amount': float(trip.final_cost_per_person),
            'currency': 'BDT',
            'tran_id': tran_id,
            'success_url': request.build_absolute_uri(reverse('payment_success')),
            'fail_url': request.build_absolute_uri(reverse('payment_fail')),
            'cancel_url': request.build_absolute_uri(reverse('payment_cancel')),
            'ipn_url': request.build_absolute_uri(reverse('payment_ipn')),
            
            # Customer info
            'cus_name': request.user.get_full_name() or request.user.username,
            'cus_email': request.user.email or f"{request.user.username}@shetrip.com",
            'cus_phone': participant.emergency_contact or '01700000000',
            'cus_add1': 'Dhaka, Bangladesh',
            'cus_city': 'Dhaka',
            'cus_postcode': '1000',
            'cus_country': 'Bangladesh',
            
            # Product info
            'product_name': f"Trip to {trip.destination}",
            'product_category': 'Travel',
            'product_profile': 'travel-goods',
        }
        
        # Create payment session
        response = sslcz.create_session(payment_data)
        
        if response.get('status') == 'SUCCESS':
            # Store session key in payment
            payment.transaction_id = response.get('sessionkey', tran_id)
            payment.save()
            
            # Redirect to SSLCommerz payment page
            gateway_url = response.get('GatewayPageURL')
            return redirect(gateway_url)
        else:
            # Payment session creation failed
            payment.payment_status = 'failed'
            payment.save()
            messages.error(request, f"Payment initialization failed: {response.get('failedreason', 'Unknown error')}")
            return redirect('organized_trip_detail', trip_id=trip_id)

    context = {
        'trip': trip,
        'participant': participant,
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'payments/trip_payment.html', context)


@csrf_exempt
def payment_success_view(request):
    """Handle successful payment callback from SSLCommerz"""
    
    # Get transaction data from POST
    val_id = request.POST.get('val_id')
    tran_id = request.POST.get('tran_id')
    amount = request.POST.get('amount')
    card_type = request.POST.get('card_type')
    bank_tran_id = request.POST.get('bank_tran_id')
    
    if not val_id or not tran_id:
        messages.error(request, 'Invalid payment response.')
        return redirect('organized_trips')
    
    # Validate transaction with SSLCommerz
    sslcz = SSLCommerzPayment()
    validation_response = sslcz.validate_transaction(val_id, tran_id)
    
    if validation_response.get('status') == 'VALID':
        # Find payment record
        try:
            payment = Payment.objects.get(transaction_id=tran_id)
            
            # Update payment status
            payment.payment_status = 'completed'
            payment.payment_method = card_type or 'sslcommerz'
            payment.save()
            
            # Update participant
            participant = TripParticipant.objects.get(trip=payment.trip, user=payment.user)
            participant.payment_status = 'paid'
            participant.amount_paid = payment.total_amount
            participant.save()
            
            # Recalculate trip status
            _recalculate_trip_status(payment.trip)
            
            messages.success(request, 'Payment successful! You have 5 minutes to request a refund if needed.')
            return redirect('organized_trip_detail', trip_id=payment.trip.trip_id)
            
        except Payment.DoesNotExist:
            messages.error(request, 'Payment record not found.')
            return redirect('organized_trips')
    else:
        messages.error(request, 'Payment validation failed.')
        return redirect('organized_trips')


@csrf_exempt
def payment_fail_view(request):
    """Handle failed payment callback from SSLCommerz"""
    tran_id = request.POST.get('tran_id')
    
    if tran_id:
        try:
            payment = Payment.objects.get(transaction_id=tran_id)
            payment.payment_status = 'failed'
            payment.save()
        except Payment.DoesNotExist:
            pass
    
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('organized_trips')


@csrf_exempt
def payment_cancel_view(request):
    """Handle cancelled payment callback from SSLCommerz"""
    tran_id = request.POST.get('tran_id')
    
    if tran_id:
        try:
            payment = Payment.objects.get(transaction_id=tran_id)
            payment.payment_status = 'failed'
            payment.save()
        except Payment.DoesNotExist:
            pass
    
    messages.warning(request, 'Payment cancelled.')
    return redirect('organized_trips')


@csrf_exempt
def payment_ipn_view(request):
    """
    Instant Payment Notification (IPN) handler
    This is called by SSLCommerz server-to-server
    """
    val_id = request.POST.get('val_id')
    tran_id = request.POST.get('tran_id')
    
    if val_id and tran_id:
        sslcz = SSLCommerzPayment()
        validation_response = sslcz.validate_transaction(val_id, tran_id)
        
        if validation_response.get('status') == 'VALID':
            try:
                payment = Payment.objects.get(transaction_id=tran_id)
                if payment.payment_status != 'completed':
                    payment.payment_status = 'completed'
                    payment.save()
                    
                    participant = TripParticipant.objects.get(trip=payment.trip, user=payment.user)
                    participant.payment_status = 'paid'
                    participant.amount_paid = payment.total_amount
                    participant.save()
                    
                    _recalculate_trip_status(payment.trip)
            except Payment.DoesNotExist:
                pass
    
    return HttpResponse('IPN received', status=200)


@login_required
@verification_required
def trip_cancel_payment_view(request, trip_id):
    """Refund - 5-minute refund window with SSLCommerz"""
    try:
        profile = request.user.userprofile
    except:
        profile = None
    
    trip = get_object_or_404(OrganizedTrip, trip_id=trip_id)
    participant = get_object_or_404(TripParticipant, trip=trip, user=request.user)

    payment = Payment.objects.filter(
        trip=trip, 
        user=request.user, 
        payment_status='completed'
    ).order_by('-payment_date').first()
    
    if not payment:
        messages.error(request, 'No payment found.')
        return redirect('organized_trip_detail', trip_id=trip_id)

    # ✅ FIXED: 5-minute refund window
    refund_deadline = payment.payment_date + timedelta(minutes=5)
    within_window = timezone.now() < refund_deadline
    
    if not within_window:
        messages.error(request, 'Refund period expired (5-minute limit).')
        return redirect('organized_trip_detail', trip_id=trip_id)

    if request.method == 'POST':
        # Initiate refund with SSLCommerz
        sslcz = SSLCommerzPayment()
        
        # Query transaction to get bank_tran_id
        query_response = sslcz.query_transaction(payment.transaction_id)
        
        if query_response.get('status') == 'VALID':
            bank_tran_id = query_response.get('bank_tran_id')
            
            # Initiate refund
            refund_response = sslcz.initiate_refund(
                bank_tran_id=bank_tran_id,
                refund_amount=payment.total_amount,
                refund_remarks='Customer requested refund within 5-minute window'
            )
            
            if refund_response.get('status') == 'success':
                payment.payment_status = 'refunded'
                payment.refund_status = True
                payment.save()

                participant.payment_status = 'refunded'
                participant.save()

                trip.total_participants -= 1
                trip.save()

                messages.success(request, 'Refund initiated successfully. Amount will be credited within 7-10 business days.')
                return redirect('organized_trips')
            else:
                messages.error(request, f"Refund failed: {refund_response.get('errorReason', 'Unknown error')}")
        else:
            messages.error(request, 'Unable to process refund. Please contact support.')

    can_refund = timezone.now() < refund_deadline

    context = {
        'trip': trip,
        'payment': payment,
        'profile': profile,
        'user': request.user,
        'can_refund': can_refund,
        'refund_deadline': refund_deadline,
    }
    return render(request, 'payments/trip_cancel_payment_confirm.html', context)


def _recalculate_trip_status(trip: OrganizedTrip) -> None:
    """Recalculate trip status when payment received"""
    paid_count = TripParticipant.objects.filter(
        trip=trip, 
        payment_status='paid'
    ).count()
    
    if paid_count >= 2 and trip.trip_status in ['open', 'planning']:
        trip.trip_status = 'confirmed'
        trip.save()


@login_required
@verification_required
def checkout_view(request, trip_id):
    """Legacy payment view - redirects to trip_payment_view"""
    return redirect('trip_payment', trip_id=trip_id)


@login_required
@verification_required
def refund_view(request, trip_id):
    """Legacy refund view - redirects to trip_cancel_payment_view"""
    return redirect('trip_cancel_payment', trip_id=trip_id)


@login_required
@verification_required
def payments_history_view(request):
    """List user's payment transactions grouped by trip"""
    profile = getattr(request.user, 'userprofile', None)
    payments = Payment.objects.filter(user=request.user).select_related('trip').order_by('-payment_date')

    # Group payments by trip
    payments_by_trip = {}
    for p in payments:
        if p.trip:
            payments_by_trip.setdefault(p.trip, []).append(p)

    grouped = [
        {
            'trip': trip,
            'payments': plist,
            'total_paid': sum([float(pp.total_amount) for pp in plist if pp.payment_status in ['completed']]),
        }
        for trip, plist in payments_by_trip.items()
    ]

    context = {
        'profile': profile,
        'user': request.user,
        'grouped_payments': grouped,
    }
    return render(request, 'payments/history.html', context)