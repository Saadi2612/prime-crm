from django.db import models
from prime_crm.utils import UUIDTimestampedModel


class Lead(UUIDTimestampedModel):
    leadgen_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    min_budget = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    max_budget = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    next_follow_up = models.DateField(blank=True, null=True)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='leads',
    )
    stage = models.ForeignKey(
        'leads.LeadStage',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='stage_leads',
    )
    form_id = models.CharField(max_length=255, blank=True, null=True)
    assigned_to = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_leads',
    )
    custom_data = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.created_time:
            self.created_time = self.created_at
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.leadgen_id})"
