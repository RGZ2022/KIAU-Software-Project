from django import forms
from .models import Resource


# Resource form
class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource

        # Form fields
        fields = ['course', 'title', 'file']

        # Labels
        labels = {
            'course': 'درس',
            'title': 'عنوان منبع',
            'file': 'فایل منبع',
        }

        # Widgets
        widgets = {
            'course': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'title': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'file': forms.FileInput(
                attrs={'class': 'form-control'}
            ),
        }