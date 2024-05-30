from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from ..serializers import TagSerializer
from core.models import Tag  # noqa

TAGS_URL = reverse("recipe:tag-list")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def create_tag(user, **params):
    default = {"name": "Sample name"}
    default.update(params)

    tag = Tag.objects.create(user=user, **default)
    return tag


def detail_url(tag_id):
    return reverse("recipe:tag-detail", args=[tag_id])


class PublicTagsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="test@example.com",
            password="password123",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        create_tag(self.user)
        create_tag(self.user, name="Second tag")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        new_user = create_user(
            email="othertest@example.com", password="otherpassword123"
        )
        create_tag(user=new_user, name="New tag")
        tag = create_tag(user=self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        tag = create_tag(user=self.user, name="Non - updated tag")

        payload = {"name": "Updated tag"}

        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        tag = create_tag(user=self.user)

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())
