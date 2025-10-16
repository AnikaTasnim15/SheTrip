from django import forms
from .models import SafetyReport, EmergencyContact, SOSAlert


class SafetyReportForm(forms.ModelForm):
    class Meta:
        model = SafetyReport
        fields = ['title', 'report_type', 'description', 'severity_level', 'location']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title of the issue'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe what happened in detail...'
            }),
            'severity_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Where did this occur? (optional)'
            }),
        }
        labels = {
            'report_type': 'Type of Issue',
            'severity_level': 'How Serious Is This?',
        }


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = ['contact_name', 'relationship', 'phone_number', 'alternate_phone', 'email', 'is_primary']
        widgets = {
            'contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name of emergency contact'
            }),
            'relationship': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+880 1XXX-XXXXXX',
                'type': 'tel'
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Alternate phone (optional)',
                'type': 'tel'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address (optional)'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_primary': 'Set as primary emergency contact',
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        # Basic validation - you can enhance this
        if phone and len(phone.replace('-', '').replace('+', '').replace(' ', '')) < 10:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone


class SOSAlertForm(forms.ModelForm):
    class Meta:
        model = SOSAlert
        fields = ['alert_type', 'description', 'location_address']
        widgets = {
            'alert_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe your emergency (optional but helpful)'
            }),
            'location_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Where are you right now?'
            }),
        }
        labels = {
            'alert_type': 'What kind of emergency?',
            'location_address': 'Your Current Location',
        }


class QuickSOSForm(forms.Form):
    """Quick SOS form with minimal fields for emergency situations"""
    alert_type = forms.ChoiceField(
        choices=SOSAlert.ALERT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-lg'
        }),
        label='Emergency Type'
    )

    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Your location (if known)'
        }),
        label='Location'
    )
