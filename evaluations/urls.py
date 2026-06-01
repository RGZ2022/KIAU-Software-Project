from django.urls import path
from . import views

app_name = "evaluations"

urlpatterns = [
    path("evaluate/<int:offering_id>/", views.evaluate_professor, name="evaluate_professor"),
    path("appeal/<int:evaluation_id>/", views.appeal_evaluation, name="appeal_evaluation"),
    path('appeals/', views.admin_appeals_list, name='admin_appeals_list'),
    path('appeals/<int:appeal_id>/update/', views.update_appeal_status, name='update_appeal_status'),
    path("professor/<int:offering_id>/evaluations/", views.professor_evaluations_list, name="professor_evaluations_list"),
    path('appeals/pending/', views.admin_pending_appeals_list, name='admin_pending_appeals_list'),
]
