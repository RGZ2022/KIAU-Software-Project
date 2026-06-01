from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from .models import Course, CourseOffering, Enrollment

User = get_user_model()


class CoursesBaseMixin:
    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="StrongPass123!",
            role="student",
        )
        self.student2 = User.objects.create_user(
            username="student2",
            email="student2@example.com",
            password="StrongPass123!",
            role="student",
        )
        self.professor = User.objects.create_user(
            username="prof1",
            email="prof1@example.com",
            password="StrongPass123!",
            role="professor",
        )
        self.professor2 = User.objects.create_user(
            username="prof2",
            email="prof2@example.com",
            password="StrongPass123!",
            role="professor",
        )
        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="StrongPass123!",
            role="admin",
        )

        self.course = Course.objects.create(
            code="CS101",
            title="Intro to CS",
            description="Basics"
        )
        self.course2 = Course.objects.create(
            code="CS102",
            title="Data Structures",
            description="DS"
        )

        self.offering = CourseOffering.objects.create(
            course=self.course,
            professor=self.professor,
            term="1405-1",
            capacity=2,
            is_active=True,
        )
        self.offering_term2 = CourseOffering.objects.create(
            course=self.course2,
            professor=self.professor,
            term="1405-2",
            capacity=3,
            is_active=True,
        )


class CourseModelsTests(CoursesBaseMixin, TestCase):
    def test_term_validator_rejects_invalid_term(self):
        obj = CourseOffering(
            course=self.course,
            professor=self.professor,
            term="1405/1",  # invalid
            capacity=10,
            is_active=True,
        )
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_unique_course_professor_term_constraint(self):
        with self.assertRaises(IntegrityError):
            CourseOffering.objects.create(
                course=self.course,
                professor=self.professor,
                term="1405-1",
                capacity=20,
                is_active=True,
            )

    def test_enrollment_term_auto_filled_from_offering(self):
        en = Enrollment.objects.create(
            student=self.student,
            offering=self.offering,
            status="active",
        )
        self.assertEqual(en.term, "1405-1")

    def test_unique_student_offering_constraint(self):
        Enrollment.objects.create(student=self.student, offering=self.offering, status="active")
        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(student=self.student, offering=self.offering, status="active")


class PublicViewsTests(CoursesBaseMixin, TestCase):
    def test_offerings_list_loads(self):
        resp = self.client.get(reverse("courses:offerings_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "CS101")
        self.assertContains(resp, "CS102")

    def test_offerings_list_term_filter(self):
        resp = self.client.get(reverse("courses:offerings_list"), {"term": "1405-1"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "CS101")
        self.assertNotContains(resp, "CS102")

    def test_course_detail_loads(self):
        resp = self.client.get(reverse("courses:course_detail", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "CS101")


class StudentEnrollmentTests(CoursesBaseMixin, TestCase):
    def test_enroll_requires_login(self):
        resp = self.client.get(reverse("courses:enroll", args=[self.offering.id]))
        self.assertEqual(resp.status_code, 302)

    def test_non_student_cannot_enroll(self):
        self.client.login(username="prof1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:enroll", args=[self.offering.id]))
        self.assertEqual(resp.status_code, 302)

    def test_student_can_enroll(self):
        self.client.login(username="student1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:enroll", args=[self.offering.id]))
        self.assertRedirects(resp, reverse("courses:my_enrollments"))
        self.assertTrue(
            Enrollment.objects.filter(student=self.student, offering=self.offering, status="active").exists()
        )

    def test_enroll_fails_if_offering_inactive(self):
        self.offering.is_active = False
        self.offering.save()

        self.client.login(username="student1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:enroll", args=[self.offering.id]))
        self.assertRedirects(resp, reverse("courses:offerings_list"))
        self.assertFalse(Enrollment.objects.filter(student=self.student, offering=self.offering).exists())

    def test_enroll_fails_if_capacity_full(self):
        Enrollment.objects.create(student=self.student, offering=self.offering, status="active")
        Enrollment.objects.create(student=self.student2, offering=self.offering, status="active")

        student3 = User.objects.create_user(
            username="student3",
            email="student3@example.com",
            password="StrongPass123!",
            role="student",
        )
        self.client.login(username="student3", password="StrongPass123!")
        resp = self.client.get(reverse("courses:enroll", args=[self.offering.id]))
        self.assertRedirects(resp, reverse("courses:offerings_list"))
        self.assertFalse(Enrollment.objects.filter(student=student3, offering=self.offering).exists())

    def test_dropped_enrollment_reactivated(self):
        Enrollment.objects.create(student=self.student, offering=self.offering, status="dropped")
        self.client.login(username="student1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:enroll", args=[self.offering.id]))
        self.assertRedirects(resp, reverse("courses:my_enrollments"))

        en = Enrollment.objects.get(student=self.student, offering=self.offering)
        self.assertEqual(en.status, "active")

    def test_my_enrollments_requires_student(self):
        self.client.login(username="prof1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:my_enrollments"))
        self.assertEqual(resp.status_code, 302)


class ProfessorViewsTests(CoursesBaseMixin, TestCase):
    def test_professor_offerings_requires_professor(self):
        self.client.login(username="student1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:professor_offerings"))
        self.assertEqual(resp.status_code, 302)

    def test_professor_offerings_only_self(self):
        CourseOffering.objects.create(
            course=self.course2,
            professor=self.professor2,
            term="1405-3",
            capacity=10,
            is_active=True,
        )
        self.client.login(username="prof1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:professor_offerings"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "CS101")
        self.assertContains(resp, "CS102")  # prof1 has CS102 offering_term2
        # offering prof2 should not appear (code may repeat in page; robust check below)
        offerings = resp.context["offerings"]
        self.assertTrue(all(o.professor_id == self.professor.id for o in offerings))

    def test_offering_students_list_only_owner_professor(self):
        Enrollment.objects.create(student=self.student, offering=self.offering, status="active")

        self.client.login(username="prof1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:offering_students", args=[self.offering.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "student1")

        self.client.logout()
        self.client.login(username="prof2", password="StrongPass123!")
        resp2 = self.client.get(reverse("courses:offering_students", args=[self.offering.id]))
        self.assertEqual(resp2.status_code, 404)  # چون get_object_or_404 با professor=request.user


class AdminViewsTests(CoursesBaseMixin, TestCase):
    def test_admin_panel_requires_admin(self):
        self.client.login(username="student1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:admin_offerings"))
        self.assertEqual(resp.status_code, 302)

    def test_admin_panel_term_filter(self):
        self.client.login(username="admin1", password="StrongPass123!")
        resp = self.client.get(reverse("courses:admin_offerings"), {"term": "1405-2"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "CS102")
        self.assertNotContains(resp, "CS101")

    def test_admin_can_create_offering(self):
        self.client.login(username="admin1", password="StrongPass123!")
        data = {
            "course": self.course.id,
            "professor": self.professor2.id,
            "capacity": 25,
            "is_active": True,
            # term عمداً ارسال نمی‌شود چون editable=False
        }
        resp = self.client.post(reverse("courses:admin_offering_create"), data)
        self.assertRedirects(resp, reverse("courses:admin_offerings"))

        self.assertTrue(
            CourseOffering.objects.filter(
                course=self.course, professor=self.professor2, capacity=25
            ).exists()
        )

    def test_admin_can_update_offering(self):
        self.client.login(username="admin1", password="StrongPass123!")
        data = {
            "course": self.course2.id,
            "professor": self.professor.id,
            "capacity": 99,
            "is_active": False,
        }
        resp = self.client.post(reverse("courses:admin_offering_edit", args=[self.offering.id]), data)
        self.assertRedirects(resp, reverse("courses:admin_offerings"))

        self.offering.refresh_from_db()
        self.assertEqual(self.offering.course_id, self.course2.id)
        self.assertEqual(self.offering.capacity, 99)
        self.assertFalse(self.offering.is_active)

    def test_admin_can_delete_offering(self):
        self.client.login(username="admin1", password="StrongPass123!")
        resp = self.client.post(reverse("courses:admin_offering_delete", args=[self.offering.id]))
        self.assertRedirects(resp, reverse("courses:admin_offerings"))
        self.assertFalse(CourseOffering.objects.filter(id=self.offering.id).exists())
