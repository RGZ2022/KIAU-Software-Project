from django.contrib.auth import login,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import RegisterForm, ProfileUpdateForm  # اضافه کردن ایمپورت فرم جدید
from django.contrib import messages  # برای نمایش پیام موفقیت‌آمیز بودن تغییرات

class UserLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        return reverse("accounts:profile")

class UserLogoutView(LogoutView):
    next_page='/'

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:profile")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})

@login_required
def profile(request):
    if request.method == "POST":
        # دریافت اطلاعات جدید و ذخیره آن‌ها در آبجکت user فعلی
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "پروفایل شما با موفقیت به‌روزرسانی شد.")
            return redirect("accounts:profile")
    else:
        # نمایش اطلاعات فعلی کاربر در فرم
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, "accounts/profile.html", {"form": form})

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        # دقت کنید: اینجا باید is_valid() باشد، نه valid()
        if form.is_valid(): 
            user = form.save()
            update_session_auth_hash(request, user)  # برای اینکه کاربر بعد از تغییر رمز، از اکانت خارج نشود
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})
