from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile
from .models import SupportTicket

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Username',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'form-control'
        })
    )

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'form-control'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")


class UserProfileEditForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'age', 'phone', 'city', 'country', 'occupation', 
            'languages', 'travel_style', 'accommodation', 
            'interests', 'dream_destinations', 'bio', 'profile_picture'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'dream_destinations': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

            class UserConnectionForm(forms.Form):
                message = forms.CharField(
                    required=False,
                    widget=forms.Textarea(attrs={
                        'placeholder': 'Add a message (optional)',
                        'rows': 3,
                        'class': 'form-control'
                    })
                )


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['name', 'email', 'phone', 'subject', 'category', 'priority', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+880 17XX XXX XXXX'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What is this about?'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Please describe your issue...'
            }),
        }

