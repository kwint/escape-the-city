import uuid
from django.db import models
from django.utils import timezone


class Post(models.Model):
    """Represents a checkpoint in the scavenger hunt with a QR code."""
    name = models.CharField(max_length=200, help_text="Naam van de post")
    description = models.TextField(help_text="Deze text wordt weergeven op de scan pagina", blank=True)
    qr_code_identifier = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    pdf_file = models.FileField(upload_to='instructions/')
    order = models.IntegerField(default=0, help_text="Order of the post in the hunt sequence")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "post"
        verbose_name_plural = "posten"

    def __str__(self):
        return f"{self.order}. {self.name}"

    def get_qr_url(self, request):
        """Returns the full URL that should be encoded in the QR code."""
        return request.build_absolute_uri(f'/scan/{self.qr_code_identifier}/')
