from django.contrib import admin
from .models import Course, CourseOffering, Enrollment

admin.site.register(Course)
admin.site.register(CourseOffering)
admin.site.register(Enrollment)
