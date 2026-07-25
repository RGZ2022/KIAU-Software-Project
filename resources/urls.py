# resources/urls.py

from django.urls import path
from . import views

app_name = "resources"   

urlpatterns =  [
    path("", views.resource_list, name="resource_list"),
    path("create/", views.resource_create, name="resource_create"),  
    path("<int:pk>/download/", views.resource_download, name="resource_download"),
]
