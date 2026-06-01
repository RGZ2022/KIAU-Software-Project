from django import forms
from .models import CourseOffering

class OfferingForm(forms.ModelForm):  # نام کلاس اینجا OfferingForm است
    class Meta:
        model = CourseOffering
        fields = [
     'course',
     'professor',
     'term',
     'capacity',
     'is_active'
     ]
        labels = {
     'course': 'درس',
     'professor': 'استاد',
     'term': 'ترم',
     'capacity': 'ظرفیت',
     'is_active': 'فعال',
     }
