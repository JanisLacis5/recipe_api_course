from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email_success(self):
        email = "test@example.com"
        password = "testpwd123"
        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test1@Example.com", "Test1@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expected_email in emails:
            user = get_user_model().objects.create_user(email, password="pwd123")
            self.assertEqual(user.email, expected_email)

    def test_no_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email="", password="pwd123")

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email="test@example.com", password="pwd123"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)