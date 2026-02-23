from django.db import models


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
