from django.db import models
from prime_crm.utils import UUIDTimestampedModel

class Lead(UUIDTimestampedModel):
    leadgen_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    custom_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.leadgen_id})"
