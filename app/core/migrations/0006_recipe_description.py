# Generated by Django 5.0.6 on 2024-05-29 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_recipe"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="description",
            field=models.TextField(blank=True),
        ),
    ]
