from django.db import models
from django.utils import timezone

from .group import Group
from .post import Post


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
