from django import forms
from .models import Resource # فرض بر این است که مدل شما این است

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['course', 'title', 'file'] # فیلدهای خودت را اینجا بنویس
        
        # تعریف برچسب‌های فارسی
        labels = {
            'course': 'درس',
            'title': 'عنوان منبع',
            'file': 'فایل منبع',
        }
        
        # اختیاری: برای استایل‌دهی بهتر (کلاس‌های CSS)
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
