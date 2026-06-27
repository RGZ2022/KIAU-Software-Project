from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

TERM_VALIDATOR = RegexValidator(
    regex=r"^\d{4}-[1-3]$",
    message="Term format must be like 1405-1"
)

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.title}"


class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="offerings")
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "professor"},
        related_name="teachings"
    )
    term = models.CharField(
    max_length=20,
    db_index=True,
    validators=[TERM_VALIDATOR],
    null=True,
    blank=True,
)
 # مثال: 1405-1
    capacity = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-term", "course__code"]
        constraints = [
            models.UniqueConstraint(fields=["course", "professor", "term"], name="uniq_course_prof_term")
        ]

    def __str__(self):
        return f"{self.course} ({self.term})"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("passed", "Passed"),
        ("dropped", "Dropped"),
    ]
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
        related_name="enrollments"
    )
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    term = models.CharField(
    max_length=20,
    db_index=True,
    validators=[TERM_VALIDATOR],
    editable=False,
    null=True,
    blank=True,
)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "offering"], name="uniq_student_offering")
        ]

    def save(self, *args, **kwargs):
        # همیشه ترم از ارائه گرفته شود
        if self.offering:
            self.term = self.offering.term
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} -> {self.offering} ({self.status})"
