from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import SafetyReport, SafetyGuideline, EmergencyContact, SOSAlert
from .forms import SafetyReportForm, EmergencyContactForm, SOSAlertForm, QuickSOSForm



def notify_emergency_contacts(alert):
    """Send Email to user's emergency contacts"""
    contacts = EmergencyContact.objects.filter(user=alert.user)

    if not contacts.exists():
        return

    # Mark as notified
    alert.contacts_notified = True
    alert.notification_sent_at = timezone.now()
    alert.save()

    for contact in contacts:
        # Email notification
        if contact.email:
            subject = f'🚨 EMERGENCY ALERT from {alert.user.get_full_name()}'

            location_url = ''
            if alert.location_latitude and alert.location_longitude:
                location_url = f'https://www.google.com/maps?q={alert.location_latitude},{alert.location_longitude}'

            message = f"""
EMERGENCY SOS ALERT

{alert.user.get_full_name()} has triggered an emergency SOS alert!

Emergency Type: {alert.get_alert_type_display()}
Time: {alert.timestamp.strftime('%B %d, %Y at %I:%M %p')}
Location: {alert.location_address or 'Not specified'}

{'View Location on Map: ' + location_url if location_url else ''}

Description: {alert.description or 'No additional details provided'}

This is an automated emergency notification from SheTrip.
If you cannot reach {alert.user.first_name}, please contact local authorities immediately.

Emergency Hotline: 999 (Bangladesh)

SheTrip Safety Team
Phone: +880 1XXX-XXXXXX
Email: safety@shetrip.com
            """

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [contact.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send email to {contact.email}: {str(e)}")


def notify_admin_team(alert):
    """Notify admin team about SOS alert"""
    User = get_user_model()
    admins = User.objects.filter(is_staff=True, is_active=True)

    if not admins.exists():
        return

    subject = f'🚨 URGENT: SOS Alert from {alert.user.get_full_name()}'

    location_url = ''
    if alert.location_latitude and alert.location_longitude:
        location_url = f'https://www.google.com/maps?q={alert.location_latitude},{alert.location_longitude}'

    # Get user profile info
    user_phone = 'Not provided'
    if hasattr(alert.user, 'profile') and alert.user.profile:
        user_phone = alert.user.profile.phone or 'Not provided'

    message = f"""
========================================
   URGENT SOS ALERT - IMMEDIATE ACTION REQUIRED
========================================

USER INFORMATION:
- Name: {alert.user.get_full_name()}
- Email: {alert.user.email}
- Phone: {user_phone}

ALERT DETAILS:
- Emergency Type: {alert.get_alert_type_display()}
- Time: {alert.timestamp.strftime('%B %d, %Y at %I:%M %p')}
- Status: {alert.get_status_display()}

LOCATION:
- Address: {alert.location_address or 'Not specified'}
{'- GPS Map: ' + location_url if location_url else '- GPS: Not available'}

DESCRIPTION:
{alert.description or 'No additional details provided'}

EMERGENCY CONTACTS NOTIFIED:
"""

    contacts = EmergencyContact.objects.filter(user=alert.user)
    if contacts.exists():
        for contact in contacts:
            primary = " [PRIMARY]" if contact.is_primary else ""
            message += f"- {contact.contact_name} ({contact.get_relationship_display()}){primary}\n"
            message += f"  Phone: {contact.phone_number}\n"
            if contact.email:
                message += f"  Email: {contact.email}\n"
    else:
        message += "⚠️ NO EMERGENCY CONTACTS SET UP\n"

    message += f"""

ADMIN ACTIONS:
- View in Admin Panel: {settings.SITE_URL}/admin/safety/sosalert/{alert.pk}/change/
- Update Status to "Responding" once help is dispatched
- Mark as "Resolved" once situation is handled

⚠️ IMMEDIATE RESPONSE REQUIRED ⚠️

SheTrip Safety System
    """

    admin_emails = [admin.email for admin in admins if admin.email]

    if admin_emails:
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send admin notification: {str(e)}")


# ==================== SAFETY CENTER ====================
@login_required
def safety_center(request):
    """Main safety center dashboard"""
    user = request.user

    # Fetch user profile
    try:
        profile = user.userprofile
    except:
        profile = None

    # Get user's emergency contacts
    emergency_contacts = EmergencyContact.objects.filter(user=user)

    # Get recent SOS alerts
    recent_sos_queryset = SOSAlert.objects.filter(user=user).order_by('-timestamp')
    recent_sos = recent_sos_queryset[:5]

    # Get user's safety reports
    user_reports_queryset = SafetyReport.objects.filter(reporter=user)
    user_reports = user_reports_queryset[:5]

    # Get featured safety guidelines
    featured_guidelines = SafetyGuideline.objects.filter(
        is_active=True,
        priority__gte=7
    )[:6]

    # Statistics
    stats = {
        'emergency_contacts_count': emergency_contacts.count(),
        'has_primary_contact': emergency_contacts.filter(is_primary=True).exists(),
        'active_sos_count': recent_sos_queryset.filter(status='active').count(),
        'reports_count': user_reports_queryset.count(),
    }

    context = {
        'emergency_contacts': emergency_contacts,
        'recent_sos': recent_sos,
        'user_reports': user_reports,
        'featured_guidelines': featured_guidelines,
        'stats': stats,
        'user': user,
        'profile': profile,
    }
    return render(request, 'safety/safety_center.html', context)


# ==================== SAFETY REPORTS ====================
def safety_list(request):
    """Public list of safety reports (anonymized)"""
    reports = SafetyReport.objects.filter(status='resolved').select_related('reporter')

    # Filter by type if provided
    report_type = request.GET.get('type')
    if report_type:
        reports = reports.filter(report_type=report_type)

    context = {
        'reports': reports,
        'report_types': SafetyReport.REPORT_TYPE_CHOICES,
    }
    return render(request, 'safety/safety_list.html', context)


def safety_detail(request, pk):
    """View details of a safety report"""
    report = get_object_or_404(SafetyReport, pk=pk)
    context = {'report': report}
    return render(request, 'safety/safety_detail.html', context)


@login_required
def safety_create(request):
    """Create a new safety report"""
    if request.method == 'POST':
        form = SafetyReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.save()
            messages.success(request, 'Your safety report has been submitted. Our team will review it shortly.')
            return redirect('safety:safety_detail', pk=report.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SafetyReportForm()

    context = {'form': form}
    return render(request, 'safety/safety_form.html', context)


@login_required
def my_reports(request):
    """View user's own safety reports"""
    reports = SafetyReport.objects.filter(reporter=request.user).order_by('-created_at')
    context = {'reports': reports}
    return render(request, 'safety/my_reports.html', context)


# ==================== SAFETY GUIDELINES ====================
def guidelines_index(request):
    """Overview page of all safety guidelines"""
    # Group guidelines by category
    guidelines_by_category = {}
    for category_key, category_name in SafetyGuideline.CATEGORY_CHOICES:
        guidelines = SafetyGuideline.objects.filter(
            category=category_key,
            is_active=True
        )
        if guidelines.exists():
            guidelines_by_category[category_name] = guidelines

    # Get high priority guidelines
    featured_guidelines = SafetyGuideline.objects.filter(
        is_active=True,
        priority__gte=8
    )[:3]

    context = {
        'guidelines_by_category': guidelines_by_category,
        'featured_guidelines': featured_guidelines,
    }
    return render(request, 'safety/guidelines/index.html', context)


def guideline_detail(request, slug):
    """View a specific safety guideline"""
    guideline = get_object_or_404(SafetyGuideline, slug=slug, is_active=True)

    # Get related guidelines from same category
    related_guidelines = SafetyGuideline.objects.filter(
        category=guideline.category,
        is_active=True
    ).exclude(slug=slug)[:3]

    context = {
        'guideline': guideline,
        'related_guidelines': related_guidelines,
    }
    return render(request, 'safety/guidelines/detail.html', context)


# Legacy guideline views (for compatibility)
def verify_before_meeting(request):
    return render(request, 'safety/guidelines/verify_before_meeting.html')


def share_location(request):
    return render(request, 'safety/guidelines/share_location.html')


def emergency_support(request):
    return render(request, 'safety/guidelines/emergency_support.html')


# ==================== EMERGENCY CONTACTS ====================
@login_required
def emergency_contacts(request):
    user = request.user

    try:
        profile = user.userprofile
    except:
        profile = None

    contacts = EmergencyContact.objects.filter(user=user).order_by('-is_primary', 'contact_name')

    context = {
        'contacts': contacts,
        'has_primary': contacts.filter(is_primary=True).exists(),
        'user': user,
        'profile': profile,
    }
    return render(request, 'safety/emergency_contacts.html', context)

@login_required
def add_emergency_contact(request):
    """Add a new emergency contact"""
    if request.method == 'POST':
        form = EmergencyContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            messages.success(request, f'{contact.contact_name} has been added as an emergency contact.')
            return redirect('safety:emergency_contacts')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmergencyContactForm()

    context = {'form': form, 'action': 'Add'}
    return render(request, 'safety/emergency_contact_form.html', context)


@login_required
def edit_emergency_contact(request, contact_id):
    """Edit an existing emergency contact"""
    contact = get_object_or_404(EmergencyContact, pk=contact_id, user=request.user)

    if request.method == 'POST':
        form = EmergencyContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, f'{contact.contact_name} has been updated.')
            return redirect('safety:emergency_contacts')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmergencyContactForm(instance=contact)

    context = {
        'form': form,
        'contact': contact,
        'action': 'Edit'
    }
    return render(request, 'safety/emergency_contact_form.html', context)


@login_required
def delete_emergency_contact(request, contact_id):
    """Delete an emergency contact"""
    contact = get_object_or_404(EmergencyContact, pk=contact_id, user=request.user)

    if request.method == 'POST':
        contact_name = contact.contact_name
        contact.delete()
        messages.success(request, f'{contact_name} has been removed from your emergency contacts.')
        return redirect('safety:emergency_contacts')

    context = {'contact': contact}
    return render(request, 'safety/emergency_contact_confirm_delete.html', context)


# ==================== SOS ALERTS ====================
@login_required
def sos_alerts(request):
    user = request.user

    try:
        profile = user.userprofile
    except:
        profile = None

    alerts = SOSAlert.objects.filter(user=user).order_by('-timestamp')

    stats = {
        'total_alerts': alerts.count(),
        'active_alerts': alerts.filter(status='active').count(),
        'resolved_alerts': alerts.filter(status='resolved').count(),
    }

    context = {
        'alerts': alerts,
        'stats': stats,
        'user': user,
        'profile': profile,
    }
    return render(request, 'safety/sos_alerts.html', context)


@login_required
def create_sos_alert(request):
    """Create a new SOS alert"""
    if request.method == 'POST':
        form = SOSAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user

            # Get location from request
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            if latitude and longitude:
                try:
                    alert.location_latitude = float(latitude)
                    alert.location_longitude = float(longitude)
                except (ValueError, TypeError):
                    pass

            alert.save()

            # Send notifications
            notify_emergency_contacts(alert)
            notify_admin_team(alert)

            messages.success(request, '🚨 SOS Alert sent! Help is on the way. Stay safe!')
            return redirect('safety:sos_alert_detail', alert_id=alert.pk)
        else:
            messages.error(request, 'Please provide alert details.')
    else:
        form = SOSAlertForm()

    # Get user's emergency contacts
    emergency_contacts = EmergencyContact.objects.filter(user=request.user)

    context = {
        'form': form,
        'emergency_contacts': emergency_contacts,
    }
    return render(request, 'safety/create_sos_alert.html', context)


@login_required
def sos_alert_detail(request, alert_id):
    """View details of an SOS alert"""
    alert = get_object_or_404(SOSAlert, pk=alert_id, user=request.user)

    context = {'alert': alert}
    return render(request, 'safety/sos_alert_detail.html', context)


@login_required
def quick_sos(request):
    """Quick SOS button - minimal form for emergencies"""
    if request.method == 'POST':
        alert_type = request.POST.get('alert_type', 'emergency')
        location = request.POST.get('location', '')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        # Create SOS alert
        alert = SOSAlert.objects.create(
            user=request.user,
            alert_type=alert_type,
            location_address=location,
            description='Quick SOS alert',
        )

        # Add GPS coordinates if available
        if latitude and longitude:
            try:
                alert.location_latitude = float(latitude)
                alert.location_longitude = float(longitude)
                alert.save()
            except (ValueError, TypeError):
                pass

        # Send notifications
        notify_emergency_contacts(alert)
        notify_admin_team(alert)

        messages.success(request, '🚨 Emergency alert sent! Help is coming!')
        return redirect('safety:sos_alert_detail', alert_id=alert.pk)

    form = QuickSOSForm()
    context = {'form': form}
    return render(request, 'safety/quick_sos.html', context)

