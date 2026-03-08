from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.utils import UUIDTimestampedModel


def default_expires_at():
    return timezone.now() + timedelta(hours=72)


class Invitation(UUIDTimestampedModel):
    class Role(models.TextChoices):
        MANAGER = 'manager', 'Manager'
        AGENT = 'agent', 'Agent'

    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, choices=Role.choices)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations',
    )
    token = models.CharField(unique=True, editable=False)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(default=default_expires_at)

    class Meta:
        verbose_name = 'Invitation'
        verbose_name_plural = 'Invitations'
        ordering = ['-created_at']

    def __str__(self):
        return f'Invitation → {self.email} as {self.get_role_display()}'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
