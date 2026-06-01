from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.forms import RegisterForm

User = get_user_model()


class RegisterFormTests(TestCase):
    def test_email_is_required(self):
        form = RegisterForm(data={
            "username": "u1",
            "email": "",
            "role": "student",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_clean_email_strips_spaces(self):
        form = RegisterForm(data={
            "username": "u2",
            "email": "   test@example.com   ",
            "role": "student",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "test@example.com")


class RegisterViewTests(TestCase):
    def test_get_register_page(self):
        url = reverse("accounts:register")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_post_register_creates_user_and_logs_in_and_redirects_profile(self):
        url = reverse("accounts:register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "role": "student",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        resp = self.client.post(url, data)

        # should redirect to profile
        self.assertRedirects(resp, reverse("accounts:profile"))

        # user created
        self.assertTrue(User.objects.filter(username="newuser").exists())

        # user logged in
        resp2 = self.client.get(reverse("accounts:profile"))
        self.assertEqual(resp2.status_code, 200)

    def test_post_register_invalid_data_renders_form_again(self):
        url = reverse("accounts:register")
        data = {
            "username": "baduser",
            "email": "bad@example.com",
            "role": "student",
            "password1": "123",   # weak + mismatch
            "password2": "456",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "error", status_code=200)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="StrongPass123!",
            role="student",
        )

    def test_profile_requires_login(self):
        url = reverse("accounts:profile")
        resp = self.client.get(url)
        # login_required redirects to login
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp.url)

    def test_profile_for_logged_in_user(self):
        self.client.login(username="student1", password="StrongPass123!")
        resp = self.client.get(reverse("accounts:profile"))
        self.assertEqual(resp.status_code, 200)


class AuthViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="StrongPass123!",
            role="student",
        )

    def test_login_success_redirects_to_profile(self):
        resp = self.client.post(reverse("accounts:login"), {
            "username": "user1",
            "password": "StrongPass123!",
        })
        self.assertRedirects(resp, reverse("accounts:profile"))

    def test_logout_redirects_to_login(self):
      self.client.login(username="user1", password="StrongPass123!")
      resp = self.client.post(reverse("accounts:logout"))
      self.assertRedirects(resp, reverse("accounts:login"))


