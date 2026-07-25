from django import forms
from .models import Evaluation, Appeal


# Evaluation form
class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation

        # Form fields
        fields = ['rating', 'comment']

        # Labels
        labels = {
            'rating': 'نمره (۱ تا ۵)',
            'comment': 'متن نظر شما درباره استاد',
        }

        # Widgets
        widgets = {
            'rating': forms.NumberInput(
                attrs={
                    'min': 1,
                    'max': 5,
                    'placeholder': 'عددی بین ۱ تا ۵'
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'نظر خود را اینجا بنویسید...'
                }
            ),
        }

    # Rating validation
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')

        if rating < 1 or rating > 5:
            raise forms.ValidationError(
                "لطفاً نمره‌ای بین ۱ تا ۵ وارد کنید."
            )

        return rating


# Appeal form
class AppealForm(forms.ModelForm):
    class Meta:
        model = Appeal

        # Form fields
        fields = ['reason']

        # Labels
        labels = {
            'reason': 'دلیل اعتراض',
        }

        # Widgets
        widgets = {
            'reason': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'دلیل اعتراض خود را اینجا بنویسید...'
                }
            ),
        }


# Appeal status form
class AppealStatusForm(forms.ModelForm):
    class Meta:
        model = Appeal

        # Form fields
        fields = ['status']

        # Widgets
        widgets = {
            'status': forms.Select(
                attrs={
                    'class': 'form-select form-select-sm'
                }
            )
        }