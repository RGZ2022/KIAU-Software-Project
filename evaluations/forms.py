from django import forms
from .models import Evaluation, Appeal

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['rating', 'comment']
        labels = {
            'rating': 'نمره (۱ تا ۵)',
            'comment': 'متن نظر شما درباره استاد',
        }
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'placeholder': 'عددی بین ۱ تا ۵'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'نظر خود را اینجا بنویسید...'}),
        }

    # اضافه کردن متد اعتبارسنجی برای نمره
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise forms.ValidationError("لطفاً نمره‌ای بین ۱ تا ۵ وارد کنید.")
        return rating

class AppealForm(forms.ModelForm):
    class Meta:
        model = Appeal
        fields = ['reason']
        labels = {
            'reason': 'دلیل اعتراض',
        }
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'دلیل اعتراض خود را اینجا بنویسید...'
            }),
        }


class AppealStatusForm(forms.ModelForm):
    class Meta:
        model = Appeal
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'})
        }
