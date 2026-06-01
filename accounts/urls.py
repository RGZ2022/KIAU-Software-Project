print("ACCOUNTS URLs LOADED")
from django.urls import path
from .views import UserLoginView, UserLogoutView, register, profile,change_password

app_name = "accounts"

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path('logout/', UserLogoutView.as_view(next_page='/'), name='logout'),
    path("register/", register, name="register"),
    path("profile/", profile, name="profile"),
    path('password/', change_password, name='change_password'),

]
