from django.db import models
from django.utils import timezone

from .group import Group


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
