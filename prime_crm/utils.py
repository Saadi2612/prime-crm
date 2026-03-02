import uuid
from django.db import models


def generate_uuid():
    """Generate a UUID for model primary keys."""
    return uuid.uuid4()


class UUIDModel(models.Model):
    """
    Abstract base model that uses UUID as primary key.
    Use this as a base class for models that need UUID primary keys.
    """
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)
    
    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    """
    Abstract base model that provides created_at and updated_at timestamps.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class UUIDTimestampedModel(UUIDModel, TimestampedModel):
    """
    Abstract base model that combines UUID primary key with timestamps.
    Use this as a base class for most models in the project.
    """
    class Meta:
        abstract = True
