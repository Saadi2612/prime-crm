from django.db import models
from prime_crm.utils import UUIDTimestampedModel


class LeadStage(UUIDTimestampedModel):
    """
    A pipeline stage that a Lead can be in.
    Admins/managers can add, edit, or delete stages.
    The default stages (New, Contacted, Negotiation, Won, Lost) are seeded
    via a data migration and carry is_default=True so they can be identified.
    """
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order (ascending).")
    is_default = models.BooleanField(
        default=False,
        help_text="True for the built-in default stages.",
    )

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
