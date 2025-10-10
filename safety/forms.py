from django import forms
from .models import SafetyReport


class SafetyReportForm(forms.ModelForm):
    class Meta:
        model = SafetyReport
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
