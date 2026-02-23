from django.db import models
from django.utils import timezone


class Tagger(models.Model):
    """Represents a tagger who can tag groups during the hunt."""
    name = models.CharField(max_length=100, help_text="Naam van de bestuurder")
    password = models.CharField(max_length=100, unique=True, help_text="Wachtwoord om in te loggen")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']
        verbose_name = "bestuurder"
        verbose_name_plural = "bestuurders"

    def __str__(self):
        return self.name
