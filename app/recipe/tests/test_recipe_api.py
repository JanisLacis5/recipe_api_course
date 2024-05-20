from unittest import TestCase
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..serializers import RecipeSerializer

from core.models import Recipe  # noqa

import uuid

RECIPES_URL = reverse("recipe:recipe-list")


def create_recipe(user, **params):
    defaults = {
        "title": "Sample recipe title",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTestRecipeApi(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email=f"user{uuid.uuid4()}@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_recipes_success(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipes_single_user(self):
        other_user = get_user_model().objects.create_user(
            email=f"otheruser{uuid.uuid4()}@example.com",
            password="otherpassword",
        )
        recipe1 = create_recipe(user=other_user)
        recipe2 = create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        response_recipe_ids = [recipe["id"] for recipe in res.data]

        self.assertEqual(len(res.data), 1)
        self.assertNotIn(recipe1.id, response_recipe_ids)
        self.assertIn(recipe2.id, response_recipe_ids)
