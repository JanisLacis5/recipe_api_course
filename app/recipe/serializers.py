from rest_framework import serializers
from django.conf import settings

from core.models import Recipe  # noqa


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields = ['id']
