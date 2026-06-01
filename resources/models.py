from django.db import models
from django.conf import settings
from courses.models import Course
from .validators import validate_file_extension, validate_file_size


class Resource(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to="resources/",
        validators=[validate_file_extension, validate_file_size]
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "professor"},
        related_name="resources"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.course})"

