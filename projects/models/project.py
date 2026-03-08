from django.db import models
from prime_crm.utils import UUIDTimestampedModel


class ProjectType(models.TextChoices):
    PLOT = 'plot', 'Plot'
    APARTMENT = 'apartment', 'Apartment'
    HOUSE = 'house', 'House'
    PORTION = 'portion', 'Portion'
    OFFICE = 'office', 'Office'
    TOWNHOUSE = 'townhouse', 'Townhouse'


class SizeUnit(models.TextChoices):
    MARLA = 'marla', 'Marla'
    SQFT = 'sqft', 'Sqft'


class Project(UUIDTimestampedModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    type = models.CharField(
        max_length=20,
        choices=ProjectType.choices,
        default=ProjectType.PLOT,
    )
    price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    form_id = models.CharField(max_length=255, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    size = models.DecimalField(max_digits=10, decimal_places=2)
    size_unit = models.CharField(
        max_length=10,
        choices=SizeUnit.choices,
        default=SizeUnit.MARLA,
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.size} {self.size_unit})"
