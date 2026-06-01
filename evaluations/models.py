from django.db import models
from django.conf import settings
from courses.models import CourseOffering


class Evaluation(models.Model):
    offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name="evaluations"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
        related_name="evaluations"
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["offering", "student"],
                name="unique_evaluation_per_student_per_offering"
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.offering} ({self.rating})"


class Appeal(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار"),
        (STATUS_ACCEPTED, "پذیرفته"),
        (STATUS_REJECTED, "رد شده"),
    ]

    evaluation = models.OneToOneField(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="appeal"
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def lock_if_decided(self):
        return self.status in [self.STATUS_ACCEPTED, self.STATUS_REJECTED]

    def __str__(self):
        return f"Appeal #{self.id} - {self.get_status_display()}"
