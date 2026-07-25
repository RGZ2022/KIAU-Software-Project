from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import RegisterForm, ProfileUpdateForm
from django.contrib import messages


# Login
class UserLoginView(LoginView):
    template_name = "accounts/login.html"

    # Redirect
    def get_success_url(self):
        return reverse("accounts:profile")


# Logout
class UserLogoutView(LogoutView):
    next_page = '/'


# Register
def register(request):
    if request.method == "POST":
        # Form data
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Save user
            user = form.save()
            login(request, user)
            return redirect("accounts:profile")
    else:
        # Empty form
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


# Profile
@login_required
def profile(request):
    if request.method == "POST":
        # Update form
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            # Success
            messages.success(request, "پروفایل شما با موفقیت به‌روزرسانی شد.")
            return redirect("accounts:profile")
    else:
        # Current data
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


# Change password
def change_password(request):
    if request.method == "POST":
        # Password form
        form = PasswordChangeForm(request.user, request.POST)

        # Validate
        if form.is_valid():
            user = form.save()

            # Keep session
            update_session_auth_hash(request, user)

            return redirect("accounts:profile")
    else:
        # Empty form
        form = PasswordChangeForm(request.user)

    return render(request, "accounts/change_password.html", {"form": form})