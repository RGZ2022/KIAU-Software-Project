# courses/urls.py
from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    path("", views.course_offerings_list, name="offerings_list"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),

    # دانشجو
    path("my-enrollments/", views.my_enrollments, name="my_enrollments"),
    path("enroll/<int:offering_id>/", views.enroll_in_offering, name="enroll"),

    # استاد
    path("professor/offerings/", views.professor_offerings_list, name="professor_offerings"),
    path("professor/offerings/<int:offering_id>/students/", views.offering_students_list, name="offering_students"),

    # ادمین
    path("admin/offerings/", views.admin_offerings_panel, name="admin_offerings"),
    path("admin/offerings/create/", views.admin_offering_create, name="admin_offering_create"),
    path("admin/offerings/<int:offering_id>/edit/", views.admin_offering_update, name="admin_offering_edit"),
    path("admin/offerings/<int:offering_id>/delete/", views.admin_offering_delete, name="admin_offering_delete"),
]
