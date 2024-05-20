from rest_framework import serializers

from core.models import Recipe  # noqa


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "title", "time_minutes", "price", "link"]
        read_only_fields = ["id"]


class RecipeDetailSerializer(RecipeSerializer):
    details = RecipeSerializer.Meta.fields + ["description"]