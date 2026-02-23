import uuid
from django.db import models
from django.utils import timezone


class Group(models.Model):
    """Represents a team participating in the scavenger hunt."""
    name = models.CharField(max_length=100)
    scout_group = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    qr_code_identifier = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    members = models.TextField(blank=True, help_text="Namen van groepsleden (één per regel)")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Contactnummer van de groep")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['scout_group', 'name']
        unique_together = ['name', 'scout_group']
        verbose_name = "groep"
        verbose_name_plural = "Groepjes"

    def __str__(self):
        return f"{self.scout_group} {self.name}"

    def get_tag_url(self, request):
        """Returns the full URL that should be encoded in the QR code for tagging."""
        return request.build_absolute_uri(f'/tag/{self.qr_code_identifier}/')
