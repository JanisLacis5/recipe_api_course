from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

import sys

sys.path.append("..")
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer  # noqa
from core.models import Recipe, Tag  # noqa

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    defaults = {
        "title": "Sample recipe title",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "description": "Sample description",
        "link": "https://example.com/recipe.pdf",
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def create_tag(user, **params):
    default = {"name": "Sample name"}
    default.update(**params)

    return Tag.objects.create(user=user, **default)


class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="test@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=self.user)

    #
    def test_retrieve_recipes(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        other_user = create_user(
            email="otheruser@example.com",
            password="otherpassword",
        )
        recipe1 = create_recipe(user=other_user)
        recipe2 = create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)

        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        payload = {
            "title": "Sample recipe",
            "time_minutes": 20,
            "price": Decimal("5.55"),
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user, title="Sample recipe title", link=original_link
        )

        payload = {"title": "New recipe title"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            time_minutes=25,
            price=Decimal("6.69"),
            link="https://example.com/recipe.pdf",
            description="Sample recipe description",
        )

        payload = {
            "title": "New recipe title",
            "time_minutes": 35,
            "price": Decimal("5.59"),
            "link": "https://newexample.com/otherrecipe.pdf",
            "description": "Sample recipe description",
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        new_user = create_user(email="othertest@example.com", password="otherpassword")
        recipe = create_recipe(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        new_user = create_user(email="newtest@example.com", password="newpassword")
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_tags(self):
        payload = {
            "title": "Sample recipe",
            "time_minutes": 30,
            "price": Decimal("2.99"),
            "tags": [{"name": "tag 1"}, {"name": "tag 2"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipes[0].tags.filter(user=self.user, name=tag["name"]).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        tag = create_tag(user=self.user, name="tag 1")

        payload = {
            "title": "Sample recipe",
            "time_minutes": 30,
            "price": Decimal("2.99"),
            "tags": [{"name": "tag 1"}, {"name": "tag 2"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)
        self.assertIn(tag, recipes[0].tags.all())
        for tag in payload["tags"]:
            exists = recipes[0].tags.filter(user=self.user, name=tag["name"]).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recipe = create_recipe(user=self.user)

        payload = {
            "title": "Updated recipe",
            "tags": [{"name": "New tag 1"}, {"name": "New tag 2"}],
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(user=self.user, name=tag["name"]).exists()
            self.assertTrue(exists)

    def test_update_recipe_assign_tag(self):
        tag_breakfast = create_tag(user=self.user, name='breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = create_tag(user=self.user, name='lunch')
        payload = {
            'tags': [{'name': 'lunch'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag = create_tag(user=self.user, name='breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {
            'tags': []
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
