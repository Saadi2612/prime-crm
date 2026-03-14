from django.db import models
from prime_crm.utils import UUIDTimestampedModel


class LeadTransfer(UUIDTimestampedModel):
    """
    Records each time a lead is reassigned (transferred) from one agent to another.

    Fields:
        lead            – the lead being transferred
        from_user       – the agent who previously held the lead (None = unassigned)
        to_user         – the agent the lead is being assigned to
        transferred_by  – the user (admin/manager) who initiated the transfer
        note            – optional context/reason for the transfer
    """
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.CASCADE,
        related_name='transfers',
    )
    from_user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers_out',
    )
    to_user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers_in',
    )
    transferred_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers_initiated',
    )
    note = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return (
            f"{self.from_user} → {self.to_user} "
            f"(lead: {self.lead_id})"
        )
