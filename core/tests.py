from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from courses.models import Course, CourseOffering, Enrollment


User = get_user_model()


class CoreViewsTestCase(TestCase):
    """تست ویوهای کلیدی مرتبط با course‌ها و پروفایل استاد در اپ core."""

    def setUp(self):
        # کاربران نمونه با مدل سفارشی
        self.student = User.objects.create_user(username="student1", password="pass123", first_name="John")
        self.professor = User.objects.create_user(username="professor1", password="pass123", first_name="Dr.")

        # تعیین نقش استاد (خیلی مهم برای ویو professor_profile)
        self.professor.role = "professor"
        self.professor.save()

        # ساخت Course بر اساس مدل موجود در courses.models
        self.course = Course.objects.create(
            code="MATH101",
            title="Mathematics",
            description="Basic math course for freshmen"
        )

        # CourseOffering + Enrollment
        self.offering = CourseOffering.objects.create(
            course=self.course,
            term="Fall 2025",
            professor=self.professor,
            is_active=True
        )

        Enrollment.objects.create(student=self.student, offering=self.offering)

    def test_course_list_view(self):
        """تست اینکه صفحه لیست ارائه‌های دروس قابل دسترسی باشد."""
        url = reverse("courses:offerings_list")
        self.client.login(username="student1", password="pass123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_enroll_view(self):
        """تست اینکه دانشجو بتواند در یک درس ثبت‌نام کند."""
        self.client.login(username="student1", password="pass123")
        url = reverse("courses:enroll", args=[self.offering.id])
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302])

    def test_my_courses_view(self):
        """تست صفحه نمایش لیست درس‌های دانشجو."""
        self.client.login(username="student1", password="pass123")
        url = reverse("courses:my_enrollments")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_professor_profile_view(self):
        """تست صفحه پروفایل استاد."""
        self.client.login(username="student1", password="pass123")
        url = reverse("core:professor_profile", kwargs={"professor_id": self.professor.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
