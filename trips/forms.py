from django import forms
from .models import TravelPlan, OrganizedTrip, TripParticipant
from datetime import date

class TravelPlanForm(forms.ModelForm):
    class Meta:
        model = TravelPlan
        fields = [
            'destination', 'start_date', 'end_date', 'purpose', 
            'budget_range', 'description', 'max_participants'
        ]
        widgets = {
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter destination (e.g., Cox\'s Bazar, Sylhet)'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'purpose': forms.Select(attrs={
                'class': 'form-control'
            }),
            'budget_range': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your travel plan, what you want to do, and what kind of travel buddy you\'re looking for...'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'max': 5,
                'value': 5
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        budget_range = cleaned_data.get('budget_range')
        
        if start_date and end_date:
            duration = (end_date - start_date).days + 1
            if duration < 2 or duration > 14:
                raise forms.ValidationError("Trip duration must be between 2 and 14 days.")
        
        if budget_range and budget_range not in dict(TravelPlan.BUDGET_CHOICES):
            raise forms.ValidationError("Invalid budget range selected.")
        return cleaned_data


class TripSearchForm(forms.Form):
    destination = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by destination...'
        })
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    budget_range = forms.ChoiceField(
        required=False,
        choices=[('', 'All Budgets')] + TravelPlan.BUDGET_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    purpose = forms.ChoiceField(
        required=False,
        choices=[('', 'All Purposes')] + TravelPlan.PURPOSE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )


class JoinTripForm(forms.Form):
    """Form for joining an organized trip"""
    emergency_contact = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+880 1234-567890'
        }),
        label="Emergency Contact Number"
    )
    
    special_requirements = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Any dietary restrictions, medical needs, or special requests...'
        }),
        label="Special Requirements"
    )
    
    agree_to_terms = forms.BooleanField(
        required=True,
        label="I agree to the trip terms and safety guidelines"
    )
    
    emergency_contact_confirmed = forms.BooleanField(
        required=True,
        label="I confirm my emergency contact is reachable"
    )