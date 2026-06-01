# resources/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from accounts.models import User
from courses.models import Course, CourseOffering
from .models import Resource
from .forms import ResourceForm
import os


class ValidatorTests(TestCase):
    """تست اعتبارسنجی‌های سفارشی"""

    def test_validate_file_extension_valid(self):
        """پسوند مجاز باید بدون خطا باشد"""
        from .validators import validate_file_extension
        for ext in ["pdf", "docx", "pptx", "zip"]:
            mock_file = SimpleUploadedFile(f"test.{ext}", b"content")
            mock_file.name = f"test.{ext}"
            try:
                validate_file_extension(mock_file)
            except ValidationError:
                self.fail(f"validate_file_extension raised error for .{ext}")

    def test_validate_file_extension_invalid(self):
        """پسوند غیرمجاز باید خطا دهد"""
        from .validators import validate_file_extension
        mock_file = SimpleUploadedFile("test.exe", b"content")
        mock_file.name = "test.exe"
        with self.assertRaises(ValidationError):
            validate_file_extension(mock_file)


class ResourceModelTests(TestCase):
    """تست مدل Resource"""

    def setUp(self):
        self.professor = User.objects.create_user(
            username="prof1",
            password="pass123",
            role="professor"
        )
        self.course = Course.objects.create(
            code="CS101",
            title="Introduction to Programming"
        )

    def test_resource_creation(self):
        """ایجاد Resource با فیلدهای صحیح"""
        resource = Resource.objects.create(
            title="Lecture 1 Slides",
            course=self.course,
            uploaded_by=self.professor,
            file=SimpleUploadedFile("slides.pdf", b"content")
        )
        self.assertEqual(resource.title, "Lecture 1 Slides")
        self.assertEqual(resource.course, self.course)
        self.assertEqual(resource.uploaded_by, self.professor)
        self.assertIsNotNone(resource.created_at)

    def test_resource_str_representation(self):
        """نمایش رشته‌ای Resource"""
        resource = Resource.objects.create(
            title="Test Resource",
            course=self.course,
            uploaded_by=self.professor,
            file=SimpleUploadedFile("test.pdf", b"content")
        )
        expected = f"Test Resource (CS101 - Introduction to Programming)"
        self.assertEqual(str(resource), expected)

    def test_resource_ordering(self):
        """ترتیب پیش‌فرض بر اساس تاریخ آپلود"""
        r1 = Resource.objects.create(
            title="Old Resource",
            course=self.course,
            uploaded_by=self.professor,
            file=SimpleUploadedFile("old.pdf", b"content")
        )
        r2 = Resource.objects.create(
            title="New Resource",
            course=self.course,
            uploaded_by=self.professor,
            file=SimpleUploadedFile("new.pdf", b"content")
        )
        resources = list(Resource.objects.all())
        self.assertEqual(resources[0], r1)
        self.assertEqual(resources[1], r2)


class ResourceFormTests(TestCase):
    """تست فرم ResourceForm"""

    def setUp(self):
        self.professor = User.objects.create_user(
            username="prof1",
            password="pass123",
            role="professor"
        )
        self.course = Course.objects.create(
            code="CS101",
            title="Programming"
        )

    def test_form_valid_data(self):
        """فرم با داده‌های صحیح باید معتبر باشد"""
        file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        form = ResourceForm(
            data={
                "title": "Test Resource",
                "course": self.course.id
            },
            files={"file": file}
        )
        self.assertTrue(form.is_valid())

    def test_form_missing_required_fields(self):
        """فرم بدون فیلدهای الزامی باید نامعتبر باشد"""
        form = ResourceForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("course", form.errors)
        self.assertIn("file", form.errors)


class ResourceListViewTests(TestCase):
    """تست نمایش لیست منابع"""

    def setUp(self):
        self.client = Client()
        self.professor = User.objects.create_user(
            username="prof1",
            password="pass123",
            role="professor"
        )
        self.student = User.objects.create_user(
            username="student1",
            password="pass123",
            role="student"
        )
        self.course = Course.objects.create(code="CS101", title="Programming")
        self.resource = Resource.objects.create(
            title="Test Resource",
            course=self.course,
            uploaded_by=self.professor,
            file=SimpleUploadedFile("test.pdf", b"content")
        )
        self.url = reverse("resource_list")

    def test_list_view_requires_login(self):
        """دسترسی به لیست نیاز به ورود دارد"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_list_view_accessible_by_authenticated_user(self):
        """کاربر وارد شده می‌تواند لیست را ببیند"""
        self.client.login(username="student1", password="pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "resources/resource_list.html")

    def test_list_view_shows_resources(self):
        """لیست باید منابع موجود را نشان دهد"""
        self.client.login(username="student1", password="pass123")
        response = self.client.get(self.url)
        self.assertContains(response, "Test Resource")
        self.assertContains(response, "Programming")

    def test_list_view_filter_by_course(self):
        """فیلتر بر اساس درس"""
        course2 = Course.objects.create(code="CS102", title="Data Structures")
        resource2 = Resource.objects.create(
            title="DS Resource",
            course=course2,
            uploaded_by=self.professor,
            file=SimpleUploadedFile("ds.pdf", b"content")
        )
        self.client.login(username="student1", password="pass123")
        response = self.client.get(self.url, {"course": self.course.id})
        self.assertContains(response, "Test Resource")
        self.assertNotContains(response, "DS Resource")


class ResourceUploadViewTests(TestCase):
    """تست آپلود منبع"""

    def setUp(self):
        self.client = Client()
        self.professor = User.objects.create_user(
            username="prof1",
            password="pass123",
            role="professor"
        )
        self.student = User.objects.create_user(
            username="student1",
            password="pass123",
            role="student"
        )
        self.course = Course.objects.create(code="CS101", title="Programming")
        self.url = reverse("resource_create")

    def test_upload_view_requires_login(self):
        """آپلود نیاز به ورود دارد"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_upload_view_requires_professor_role(self):
        """فقط استاد می‌تواند آپلود کند"""
        self.client.login(username="student1", password="pass123")
        response = self.client.get(self.url)
        # اگر redirect می‌شود به جای 403
        self.assertIn(response.status_code, [302, 403])

    def test_upload_view_accessible_by_professor(self):
        """استاد می‌تواند به صفحه آپلود دسترسی داشته باشد"""
        self.client.login(username="prof1", password="pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "resources/resource_form.html")

    def test_upload_resource_success(self):
        """آپلود موفق منبع"""
        self.client.login(username="prof1", password="pass123")
        file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        response = self.client.post(self.url, {
            "title": "New Resource",
            "course": self.course.id,
            "file": file
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Resource.objects.filter(title="New Resource").exists())
        resource = Resource.objects.get(title="New Resource")
        self.assertEqual(resource.uploaded_by, self.professor)

    def test_upload_invalid_file_type(self):
        """آپلود فایل با پسوند نامعتبر"""
        self.client.login(username="prof1", password="pass123")
        file = SimpleUploadedFile("test.exe", b"content")
        file.name = "test.exe"
        response = self.client.post(self.url, {
            "title": "Invalid File",
            "course": self.course.id,
            "file": file
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Resource.objects.filter(title="Invalid File").exists())


class ResourceDownloadViewTests(TestCase):
    """تست دانلود منبع"""

    def setUp(self):
        self.client = Client()
        self.professor = User.objects.create_user(
            username="prof1",
            password="pass123",
            role="professor"
        )
        self.student = User.objects.create_user(
            username="student1",
            password="pass123",
            role="student"
        )
        self.course = Course.objects.create(code="CS101", title="Programming")
        self.resource = Resource.objects.create(
            title="Test Resource",
            course=self.course,
            uploaded_by=self.professor,
            file=SimpleUploadedFile("test.pdf", b"test content")
        )
        self.url = reverse("resource_download", kwargs={"pk": self.resource.pk})

    def test_download_requires_login(self):
        """دانلود نیاز به ورود دارد"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_download_accessible_by_authenticated_user(self):
        """کاربر وارد شده می‌تواند دانلود کند"""
        self.client.login(username="student1", password="pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_download_nonexistent_resource(self):
        """دانلود منبع ناموجود باید 404 برگرداند"""
        self.client.login(username="student1", password="pass123")
        url = reverse("resource_download", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ResourceIntegrationTests(TestCase):
    """تست‌های یکپارچه سناریوهای واقعی"""

    def setUp(self):
        self.client = Client()
        self.professor = User.objects.create_user(
            username="prof1",
            password="pass123",
            role="professor"
        )
        self.student = User.objects.create_user(
            username="student1",
            password="pass123",
            role="student"
        )
        self.course = Course.objects.create(code="CS101", title="Programming")
        self.offering = CourseOffering.objects.create(
            course=self.course,
            professor=self.professor,
            term="1405-1",
            capacity=30
        )

    def test_full_resource_lifecycle(self):
        """سناریوی کامل: آپلود، لیست، دانلود"""
        self.client.login(username="prof1", password="pass123")
        file = SimpleUploadedFile("lecture.pdf", b"lecture content", content_type="application/pdf")
        upload_url = reverse("resource_create")
        response = self.client.post(upload_url, {
            "title": "Lecture 1",
            "course": self.course.id,
            "file": file
        })
        self.assertEqual(response.status_code, 302)

        self.client.login(username="student1", password="pass123")
        list_url = reverse("resource_list")
        response = self.client.get(list_url)
        self.assertContains(response, "Lecture 1")

        resource = Resource.objects.get(title="Lecture 1")
        download_url = reverse("resource_download", kwargs={"pk": resource.pk})
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_upload(self):
        """دانشجو نمی‌تواند منبع آپلود کند"""
        self.client.login(username="student1", password="pass123")
        upload_url = reverse("resource_create")
        file = SimpleUploadedFile("test.pdf", b"content")
        response = self.client.post(upload_url, {
            "title": "Unauthorized Upload",
            "course": self.course.id,
            "file": file
        })
        # اگر redirect می‌شود یا 403 برمی‌گرداند
        self.assertIn(response.status_code, [302, 403])
        self.assertFalse(Resource.objects.filter(title="Unauthorized Upload").exists())

    def test_multiple_resources_same_course(self):
        """چند منبع برای یک درس"""
        self.client.login(username="prof1", password="pass123")
        upload_url = reverse("resource_create")

        for i in range(3):
            file = SimpleUploadedFile(f"lecture{i}.pdf", b"content")
            self.client.post(upload_url, {
                "title": f"Lecture {i+1}",
                "course": self.course.id,
                "file": file
            })

        self.assertEqual(Resource.objects.filter(course=self.course).count(), 3)

        self.client.login(username="student1", password="pass123")
        list_url = reverse("resource_list")
        response = self.client.get(list_url, {"course": self.course.id})
        for i in range(3):
            self.assertContains(response, f"Lecture {i+1}")

    def test_professor_can_see_own_uploads(self):
        """استاد می‌تواند آپلودهای خود را ببیند"""
        self.client.login(username="prof1", password="pass123")
        upload_url = reverse("resource_create")
        file = SimpleUploadedFile("my_lecture.pdf", b"content")
        self.client.post(upload_url, {
            "title": "My Lecture",
            "course": self.course.id,
            "file": file
        })

        list_url = reverse("resource_list")
        response = self.client.get(list_url)
        self.assertContains(response, "My Lecture")

    def test_empty_resource_list(self):
        """لیست خالی منابع"""
        self.client.login(username="student1", password="pass123")
        list_url = reverse("resource_list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['resources']), 0)

    def test_filter_returns_correct_resources(self):
        """فیلتر درس صحیح کار می‌کند"""
        course2 = Course.objects.create(code="CS102", title="Data Structures")
        
        self.client.login(username="prof1", password="pass123")
        upload_url = reverse("resource_create")
        
        file1 = SimpleUploadedFile("cs101.pdf", b"content")
        self.client.post(upload_url, {
            "title": "CS101 Resource",
            "course": self.course.id,
            "file": file1
        })
        
        file2 = SimpleUploadedFile("cs102.pdf", b"content")
        self.client.post(upload_url, {
            "title": "CS102 Resource",
            "course": course2.id,
            "file": file2
        })

        self.client.login(username="student1", password="pass123")
        list_url = reverse("resource_list")
        response = self.client.get(list_url, {"course": course2.id})
        self.assertContains(response, "CS102 Resource")
        self.assertNotContains(response, "CS101 Resource")
