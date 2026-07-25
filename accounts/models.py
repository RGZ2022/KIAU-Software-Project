from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Roles
    ROLE_CHOICES = [
        ("student", "Student"),
        ("professor", "Professor"),
        ("admin", "Admin"),
    ]

    # User role
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="student"
    )