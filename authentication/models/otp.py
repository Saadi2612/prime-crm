from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.utils import UUIDTimestampedModel


def default_otp_expires_at():
    return timezone.now() + timedelta(minutes=2)


class OTPCode(UUIDTimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='otp_codes',
    )
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(default=default_otp_expires_at)

    class Meta:
        verbose_name = 'OTP Code'
        verbose_name_plural = 'OTP Codes'
        ordering = ['-created_at']

    def __str__(self):
        return f'OTP for {self.user.email} — {"used" if self.is_used else "active"}'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
