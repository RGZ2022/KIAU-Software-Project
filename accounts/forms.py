from django import forms
from .models import User

class RegisterForm(forms.ModelForm):
    # تعریف گزینه‌ها بدون ادمین
    ROLE_CHOICES = [
        ('student', 'دانشجو'),
        ('professor', 'استاد'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, 
        label="نقش کاربری",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # تعریف فیلدهای پسورد به صورت دستی برای تاییدیه
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={'placeholder': '********'})
    )
    confirm_password = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput(attrs={'placeholder': '********'})
    )

    class Meta:
        model = User
        # فیلد پسورد اصلی مدل را اینجا می‌آوریم
        fields = ['username', 'email', 'role', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["email"].label = "آدرس ایمیل"
        self.fields["username"].label = "نام کاربری"

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise forms.ValidationError("وارد کردن ایمیل الزامی است.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("رمز عبور و تکرار آن با هم مطابقت ندارند.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # بسیار مهم: هش کردن پسورد قبل از ذخیره در دیتابیس
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
