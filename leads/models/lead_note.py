from django.db import models
from prime_crm.utils import UUIDTimestampedModel


class LeadNote(UUIDTimestampedModel):
    """
    An immutable note attached to a Lead.

    Notes are append-only: once created they cannot be edited or deleted
    via the API (the viewset intentionally exposes only list + create).
    """
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.CASCADE,
        related_name='notes',
    )
    body = models.TextField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        preview = self.body[:40] + ('…' if len(self.body) > 40 else '')
        return f"Note on {self.lead_id}: {preview}"
