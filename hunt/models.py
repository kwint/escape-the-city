import uuid
from django.db import models
from django.utils import timezone


class Group(models.Model):
    """Represents a team participating in the scavenger hunt."""
    name = models.CharField(max_length=100)
    scout_group = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
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


class Scan(models.Model):
    """Records when a group scans a post's QR code."""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='scans')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='scans')
    scanned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-scanned_at']
        unique_together = ['group', 'post']
        

    def __str__(self):
        return f"{self.group} - {self.post.name} at {self.scanned_at}"


class Tag(models.Model):
    """Records when a group is tagged by a tagger (penalty: -1 point)."""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='tags')
    tagger_name = models.CharField(max_length=100, help_text="Naam van de tagger")
    tagged_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-tagged_at']
        verbose_name = "tag"
        verbose_name_plural = "tags"

    def __str__(self):
        return f"{self.group} getagd door {self.tagger_name} om {self.tagged_at}"


class GameSettings(models.Model):
    """
    Singleton model to store game configuration.
    Only one instance should exist - editable through admin.
    """
    starting_points = models.IntegerField(
        default=20,
        help_text="Aantal punten waarmee elke groep begint"
    )
    points_per_scan = models.IntegerField(
        default=20,
        help_text="Aantal punten per gescande post"
    )
    tag_penalty = models.IntegerField(
        default=1,
        help_text="Aantal punten aftrek per tag"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Game Instellingen"
        verbose_name_plural = "Game Instellingen"

    def __str__(self):
        return f"Game Instellingen (Start: {self.starting_points}, Per Scan: {self.points_per_scan}, Tag Straf: {self.tag_penalty})"

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of settings."""
        pass

    @classmethod
    def load(cls):
        """Get or create the singleton settings instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
