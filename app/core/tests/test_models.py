from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from .. import models


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class ModelTests(TestCase):

    def test_create_user_with_email_success(self):
        email = "test@example.com"
        password = "testpassword123"
        user = create_user(email=email, password=password)

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
            user = create_user(email=email, password="passsword123")
            self.assertEqual(user.email, expected_email)

    def test_no_email_raises_error(self):
        with self.assertRaises(ValueError):
            create_user(email="", password="passsword123")

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email="test@example.com", password="passsword123"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = create_user(email="test@example.com", password="passsword123")
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample recipe name",
            time_minutes=5,
            price=Decimal("5.50"),
            description="Sample recipe description",
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        user = create_user(email="test@example.com", password="password123")
        tag = models.Tag.objects.create(user=user, name="Sample tag")

        self.assertEqual(str(tag), tag.name)
