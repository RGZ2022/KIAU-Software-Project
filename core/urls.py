from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import redirect_dashboard

app_name = "core"

urlpatterns = [
     path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("professor/<int:professor_id>/", views.professor_profile, name="professor_profile"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("professor/<int:professor_id>/ajax/submit/", views.ajax_submit_evaluation, name="ajax_submit"),
    path('dashboard/student/', views.dashboard_student, name='dashboard_student' ),
    path('dashboard/professor/', views.dashboard_professor, name='dashboard_professor'),
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("redirect/", redirect_dashboard, name="redirect-dashboard"),
    path('my-courses/', views.my_courses, name='my_courses'), 
]
